using System.Net;
using System.Text;
using System.Text.Json;

namespace Trs.Sdk;

public sealed class TrsClient
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private readonly HttpClient _http;
    private readonly string _baseUrl;

    public TrsClient(string baseUrl, TimeSpan? timeout = null, HttpClient? httpClient = null)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _http = httpClient ?? new HttpClient();
        _http.Timeout = timeout ?? TimeSpan.FromSeconds(5);
    }

    public async Task<HealthStatus> HealthAsync(CancellationToken cancellationToken = default)
    {
        var payload = await SendAsync(HttpMethod.Get, "/health", null, cancellationToken);
        return DeserializeRequired<HealthStatus>(payload, "health response");
    }

    public async Task<SubmitResult> SubmitAsync(Dictionary<string, object?> record, CancellationToken cancellationToken = default)
    {
        var payload = await SendAsync(
            HttpMethod.Post,
            "/submit",
            JsonSerializer.SerializeToElement(new Dictionary<string, object?> { ["record"] = record }, JsonOptions),
            cancellationToken);
        var result = DeserializeRequired<SubmitResult>(payload, "submit response");
        if (!result.Accepted)
        {
            throw new TrsValidationException("record rejected by verifier", result.Errors);
        }
        return result;
    }

    public async Task<IReadOnlyList<Dictionary<string, JsonElement>>> QueryAsync(
        Dictionary<string, object?> expression,
        CancellationToken cancellationToken = default)
    {
        var payload = await SendAsync(
            HttpMethod.Post,
            "/query",
            JsonSerializer.SerializeToElement(new Dictionary<string, object?> { ["query"] = expression }, JsonOptions),
            cancellationToken);
        if (!payload.TryGetProperty("records", out var recordsElement) || recordsElement.ValueKind != JsonValueKind.Array)
        {
            throw new TrsProtocolException("records must be an array");
        }
        var outRecords = new List<Dictionary<string, JsonElement>>();
        foreach (var item in recordsElement.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Object)
            {
                throw new TrsProtocolException("record must be an object");
            }
            outRecords.Add(JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(item.GetRawText(), JsonOptions) ?? []);
        }
        return outRecords;
    }

    public async Task<SyncResult> SyncAsync(
        IReadOnlyList<Dictionary<string, object?>> records,
        CancellationToken cancellationToken = default)
    {
        var payload = await SendAsync(
            HttpMethod.Post,
            "/sync",
            JsonSerializer.SerializeToElement(new Dictionary<string, object?> { ["records"] = records }, JsonOptions),
            cancellationToken);
        return DeserializeRequired<SyncResult>(payload, "sync response");
    }

    public async Task<Dictionary<string, JsonElement>> ReplayAsync(CancellationToken cancellationToken = default)
    {
        var payload = await SendAsync(
            HttpMethod.Post,
            "/replay",
            JsonSerializer.SerializeToElement(new Dictionary<string, object?>(), JsonOptions),
            cancellationToken);
        return JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(payload.GetRawText(), JsonOptions)
            ?? throw new TrsProtocolException("replay response must be an object");
    }

    private async Task<JsonElement> SendAsync(
        HttpMethod method,
        string path,
        JsonElement? jsonBody,
        CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(method, _baseUrl + path);
        request.Headers.Add("Accept", "application/json");
        if (jsonBody is not null)
        {
            request.Content = new StringContent(jsonBody.Value.GetRawText(), Encoding.UTF8, "application/json");
        }

        HttpResponseMessage response;
        try
        {
            response = await _http.SendAsync(request, cancellationToken);
        }
        catch (Exception ex)
        {
            throw new TrsConnectionException(ex.Message, ex);
        }

        var raw = await response.Content.ReadAsStringAsync(cancellationToken);
        JsonElement payload;
        try
        {
            payload = string.IsNullOrWhiteSpace(raw) ? JsonDocument.Parse("{}").RootElement.Clone() : JsonDocument.Parse(raw).RootElement.Clone();
        }
        catch (Exception ex)
        {
            throw new TrsProtocolException($"invalid JSON response from trs-node: {ex.Message}");
        }

        if (response.IsSuccessStatusCode)
        {
            return payload;
        }

        var message = ExtractErrorMessage(payload, response.StatusCode);
        if ((int)response.StatusCode >= 400 && (int)response.StatusCode < 500)
        {
            throw new TrsValidationException(message, []);
        }
        throw new TrsServerException(message);
    }

    private static string ExtractErrorMessage(JsonElement payload, HttpStatusCode statusCode)
    {
        if (payload.ValueKind == JsonValueKind.Object)
        {
            if (payload.TryGetProperty("detail", out var detail) && detail.ValueKind == JsonValueKind.String)
            {
                var detailText = detail.GetString();
                if (!string.IsNullOrWhiteSpace(detailText))
                {
                    return detailText;
                }
            }
            if (payload.TryGetProperty("error", out var error) && error.ValueKind == JsonValueKind.String)
            {
                var errorText = error.GetString();
                if (!string.IsNullOrWhiteSpace(errorText))
                {
                    return errorText;
                }
            }
        }
        return $"http {(int)statusCode}";
    }

    private static T DeserializeRequired<T>(JsonElement payload, string label)
    {
        try
        {
            return JsonSerializer.Deserialize<T>(payload.GetRawText(), JsonOptions)
                ?? throw new TrsProtocolException($"{label} must be an object");
        }
        catch (TrsProtocolException)
        {
            throw;
        }
        catch (Exception ex)
        {
            throw new TrsProtocolException($"{label} must be an object: {ex.Message}");
        }
    }
}

