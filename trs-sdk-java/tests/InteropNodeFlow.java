package dev.trs.sdk;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class InteropNodeFlow {
    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException("usage: InteropNodeFlow <base_url> <output_path>");
        }
        String baseUrl = args[0];
        Path outputPath = Path.of(args[1]);

        TRSClient client = new TRSClient(baseUrl, Duration.ofSeconds(5));
        HealthStatus health = client.health();

        Map<String, Object> observation = new LinkedHashMap<>();
        observation.put("id", "java-obs-1");
        observation.put("type", "Observation");
        observation.put("author", "java-sdk");
        observation.put("timestamp", "2026-08-05T15:05:02+00:00");
        observation.put("schema", "trs.observation.v1");
        observation.put("payload", Map.of("subject", "interop", "value", 2));
        observation.put("causes", List.of());
        observation.put("authorization", List.of());
        observation.put("signature", "sig:java-obs-1");
        SubmitResult submit = client.submit(observation);

        Map<String, Object> intention = new LinkedHashMap<>();
        intention.put("id", "java-int-1");
        intention.put("type", "Intention");
        intention.put("author", "java-sdk");
        intention.put("timestamp", "2026-08-05T15:05:03+00:00");
        intention.put("schema", "trs.intention.v1");
        intention.put("payload", Map.of("goal", "interop-check", "horizon", "cycle0012"));
        intention.put("causes", List.of("java-obs-1"));
        intention.put("authorization", List.of());
        intention.put("signature", "sig:java-int-1");

        SyncResult sync = client.sync(List.of(intention));
        List<Map<String, Object>> records = client.query(Map.of("author", "java-sdk"));
        Map<String, Object> replay = client.replay();

        List<?> unresolved = List.of();
        Object coordination = replay.get("coordination");
        if (coordination instanceof Map<?, ?> map) {
            Object unresolvedRaw = map.get("unresolved_intentions");
            if (unresolvedRaw instanceof List<?> values) {
                unresolved = values;
            }
        }

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("sdk", "java");
        summary.put("base_url", baseUrl);
        summary.put(
                "health",
                Map.of("status", health.status(), "runtime", health.runtime(), "node", health.node()));
        summary.put(
                "submit",
                Map.of(
                        "accepted", submit.accepted(),
                        "record_id", submit.recordId(),
                        "errors", submit.errors()));
        summary.put(
                "sync",
                Map.of(
                        "accepted_count", sync.acceptedCount(),
                        "rejected_count", sync.rejectedCount(),
                        "appended_ids", sync.appendedIds(),
                        "rejected_errors", sync.rejectedErrors()));
        summary.put("query_author_count", records.size());
        summary.put("replay_unresolved_intentions", unresolved);

        String json = Jsons.stringify(summary);
        Files.writeString(outputPath, json, StandardCharsets.UTF_8);
        System.out.println(json);
    }
}
