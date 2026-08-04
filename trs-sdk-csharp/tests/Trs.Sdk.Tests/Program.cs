using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using Trs.Sdk;

await Tests.RunAllAsync();

internal static class Tests
{
    public static async Task RunAllAsync()
    {
        await HealthSubmitQuerySyncReplayAsync();
        await SubmitValidationErrorAsync();
        await TimeoutConnectionErrorAsync();
        Console.WriteLine("All trs-sdk-csharp tests passed.");
    }

    private static async Task HealthSubmitQuerySyncReplayAsync()
    {
        await using var server = new TestServer(delayMs: 0);
        var client = new TrsClient(server.BaseUrl, TimeSpan.FromSeconds(2));

        var health = await client.HealthAsync();
        AssertEqual("ok", health.Status, "health status");

        await client.SubmitAsync(new Dictionary<string, object?>
        {
            ["id"] = "g1",
            ["type"] = "Observation",
            ["payload"] = new Dictionary<string, object?> { ["subject"] = "boot", ["value"] = 1 }
        });

        var rows = await client.QueryAsync(new Dictionary<string, object?>());
        AssertEqual(1, rows.Count, "query count");

        var sync = await client.SyncAsync(new List<Dictionary<string, object?>>
        {
            new()
            {
                ["id"] = "g1",
                ["type"] = "Observation",
                ["payload"] = new Dictionary<string, object?> { ["subject"] = "boot", ["value"] = 1 }
            }
        });
        AssertEqual(1, sync.AcceptedCount, "sync accepted count");

        var replay = await client.ReplayAsync();
        AssertTrue(replay.ContainsKey("coordination"), "replay contains coordination");
    }

    private static async Task SubmitValidationErrorAsync()
    {
        await using var server = new TestServer(delayMs: 0);
        var client = new TrsClient(server.BaseUrl, TimeSpan.FromSeconds(2));

        try
        {
            await client.SubmitAsync(new Dictionary<string, object?>
            {
                ["id"] = "bad",
                ["type"] = "Observation",
                ["payload"] = new Dictionary<string, object?>()
            });
            throw new Exception("expected TrsValidationException");
        }
        catch (TrsValidationException)
        {
        }
    }

    private static async Task TimeoutConnectionErrorAsync()
    {
        await using var server = new TestServer(delayMs: 250);
        var client = new TrsClient(server.BaseUrl, TimeSpan.FromMilliseconds(20));
        try
        {
            await client.HealthAsync();
            throw new Exception("expected TrsConnectionException");
        }
        catch (TrsConnectionException)
        {
        }
    }

    private static void AssertEqual<T>(T expected, T actual, string label)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new Exception($"{label}: expected={expected}, actual={actual}");
        }
    }

    private static void AssertTrue(bool value, string label)
    {
        if (!value)
        {
            throw new Exception($"{label}: expected true");
        }
    }
}

internal sealed class TestServer : IAsyncDisposable
{
    private readonly TcpListener _listener;
    private readonly CancellationTokenSource _cts = new();
    private readonly Task _loopTask;
    private readonly List<Dictionary<string, object?>> _records = [];
    private readonly int _delayMs;

    public TestServer(int delayMs)
    {
        _delayMs = delayMs;
        _listener = new TcpListener(IPAddress.Loopback, 0);
        _listener.Start();
        BaseUrl = $"http://127.0.0.1:{((IPEndPoint)_listener.LocalEndpoint).Port}";
        _loopTask = Task.Run(AcceptLoopAsync);
    }

    public string BaseUrl { get; }

    private async Task AcceptLoopAsync()
    {
        while (!_cts.IsCancellationRequested)
        {
            TcpClient? client = null;
            try
            {
                client = await _listener.AcceptTcpClientAsync(_cts.Token);
                _ = Task.Run(() => HandleClientAsync(client));
            }
            catch (OperationCanceledException)
            {
                client?.Dispose();
                break;
            }
            catch
            {
                client?.Dispose();
                if (_cts.IsCancellationRequested)
                {
                    break;
                }
            }
        }
    }

    private async Task HandleClientAsync(TcpClient client)
    {
        using var _ = client;
        using var stream = client.GetStream();

        if (_delayMs > 0)
        {
            await Task.Delay(_delayMs);
        }

        var buffer = new byte[64 * 1024];
        var read = await stream.ReadAsync(buffer);
        if (read <= 0)
        {
            return;
        }
        var request = Encoding.UTF8.GetString(buffer, 0, read);
        var firstLine = request.Split("\r\n", StringSplitOptions.None).FirstOrDefault() ?? "";
        var body = "";
        var split = request.IndexOf("\r\n\r\n", StringComparison.Ordinal);
        if (split >= 0 && split + 4 < request.Length)
        {
            body = request[(split + 4)..];
        }

        var payload = Route(firstLine, body);
        var payloadBytes = Encoding.UTF8.GetBytes(payload);
        var response = $"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {payloadBytes.Length}\r\nConnection: close\r\n\r\n";
        var headerBytes = Encoding.UTF8.GetBytes(response);
        await stream.WriteAsync(headerBytes);
        await stream.WriteAsync(payloadBytes);
        await stream.FlushAsync();
    }

    private string Route(string startLine, string body)
    {
        if (startLine.StartsWith("GET /health ", StringComparison.Ordinal))
        {
            return """{"status":"ok","runtime":"1.0.0","node":"0.1.0"}""";
        }
        if (startLine.StartsWith("POST /submit ", StringComparison.Ordinal))
        {
            var root = JsonDocument.Parse(string.IsNullOrWhiteSpace(body) ? "{}" : body).RootElement;
            var record = root.TryGetProperty("record", out var r) ? r : default;
            var payload = record.TryGetProperty("payload", out var p) ? p : default;
            var hasRequired = payload.ValueKind == JsonValueKind.Object
                && (payload.TryGetProperty("subject", out _) || payload.TryGetProperty("goal", out _) || payload.TryGetProperty("action", out _));
            var rid = record.TryGetProperty("id", out var id) ? id.GetString() ?? "" : "";
            if (!hasRequired)
            {
                return $@"{{""accepted"":false,""record_id"":""{rid}"",""errors"":[""5.3 Payload Shape""]}}";
            }
            var dict = JsonSerializer.Deserialize<Dictionary<string, object?>>(record.GetRawText()) ?? [];
            _records.Add(dict);
            return $@"{{""accepted"":true,""record_id"":""{rid}"",""errors"":[]}}";
        }
        if (startLine.StartsWith("POST /query ", StringComparison.Ordinal))
        {
            return JsonSerializer.Serialize(new Dictionary<string, object?> { ["records"] = _records });
        }
        if (startLine.StartsWith("POST /sync ", StringComparison.Ordinal))
        {
            return """{"accepted_count":1,"rejected_count":0,"appended_ids":["g1"],"rejected_errors":[]}""";
        }
        if (startLine.StartsWith("POST /replay ", StringComparison.Ordinal))
        {
            return """{"coordination":{"unresolved_intentions":[]}}""";
        }
        return """{"error":"not found"}""";
    }

    public async ValueTask DisposeAsync()
    {
        _cts.Cancel();
        _listener.Stop();
        try
        {
            await _loopTask;
        }
        catch
        {
        }
        _cts.Dispose();
    }
}
