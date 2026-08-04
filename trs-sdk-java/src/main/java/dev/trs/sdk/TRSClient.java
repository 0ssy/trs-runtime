package dev.trs.sdk;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class TRSClient {
    private final HTTPTransport transport;

    public TRSClient(String baseUrl) {
        this(baseUrl, Duration.ofSeconds(5));
    }

    public TRSClient(String baseUrl, Duration timeout) {
        this.transport = new HTTPTransport(baseUrl, timeout);
    }

    public HealthStatus health() {
        Object payload = transport.get("/health");
        Map<String, Object> obj = asObject(payload, "health response");
        return new HealthStatus(
                asString(obj.get("status")),
                asString(obj.get("runtime")),
                asString(obj.get("node")));
    }

    public SubmitResult submit(Map<String, Object> record) {
        Object payload = transport.post("/submit", Map.of("record", record));
        Map<String, Object> obj = asObject(payload, "submit response");
        boolean accepted = asBoolean(obj.get("accepted"));
        String recordId = asString(obj.get("record_id"));
        List<String> errors = asStringList(obj.get("errors"), "errors");
        SubmitResult out = new SubmitResult(accepted, recordId, errors);
        if (!accepted) {
            throw new TRSValidationError("record rejected by verifier", errors);
        }
        return out;
    }

    public List<Map<String, Object>> query(Map<String, Object> expr) {
        Object payload = transport.post("/query", Map.of("query", expr));
        Map<String, Object> obj = asObject(payload, "query response");
        Object recordsObj = obj.get("records");
        if (!(recordsObj instanceof List<?> list)) {
            throw new TRSProtocolError("records must be an array");
        }
        List<Map<String, Object>> records = new ArrayList<>();
        for (Object item : list) {
            records.add(asObject(item, "record"));
        }
        return records;
    }

    public SyncResult sync(List<Map<String, Object>> records) {
        Object payload = transport.post("/sync", Map.of("records", records));
        Map<String, Object> obj = asObject(payload, "sync response");
        int accepted = asInt(obj.get("accepted_count"));
        int rejected = asInt(obj.get("rejected_count"));
        List<String> appended = asStringList(obj.get("appended_ids"), "appended_ids");
        List<List<String>> rejectedErrors = asStringListList(obj.get("rejected_errors"), "rejected_errors");
        return new SyncResult(accepted, rejected, appended, rejectedErrors);
    }

    public Map<String, Object> replay() {
        Object payload = transport.post("/replay", Map.of());
        return asObject(payload, "replay response");
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> asObject(Object value, String label) {
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        throw new TRSProtocolError(label + " must be an object");
    }

    private static String asString(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    private static boolean asBoolean(Object value) {
        return value instanceof Boolean b && b;
    }

    private static int asInt(Object value) {
        if (value instanceof Number n) {
            return n.intValue();
        }
        return 0;
    }

    private static List<String> asStringList(Object value, String label) {
        if (!(value instanceof List<?> list)) {
            throw new TRSProtocolError(label + " must be an array");
        }
        List<String> out = new ArrayList<>();
        for (Object item : list) {
            out.add(String.valueOf(item));
        }
        return out;
    }

    private static List<List<String>> asStringListList(Object value, String label) {
        if (!(value instanceof List<?> list)) {
            throw new TRSProtocolError(label + " must be an array");
        }
        List<List<String>> out = new ArrayList<>();
        for (Object item : list) {
            out.add(asStringList(item, label + " entry"));
        }
        return out;
    }
}

