using System.Text.Json.Serialization;

namespace Trs.Sdk;

public sealed record HealthStatus(
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("runtime")] string Runtime,
    [property: JsonPropertyName("node")] string Node);

public sealed record SubmitResult(
    [property: JsonPropertyName("accepted")] bool Accepted,
    [property: JsonPropertyName("record_id")] string RecordId,
    [property: JsonPropertyName("errors")] IReadOnlyList<string> Errors);

public sealed record SyncResult(
    [property: JsonPropertyName("accepted_count")] int AcceptedCount,
    [property: JsonPropertyName("rejected_count")] int RejectedCount,
    [property: JsonPropertyName("appended_ids")] IReadOnlyList<string> AppendedIds,
    [property: JsonPropertyName("rejected_errors")] IReadOnlyList<IReadOnlyList<string>> RejectedErrors);

