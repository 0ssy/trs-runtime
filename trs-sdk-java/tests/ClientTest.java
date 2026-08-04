package dev.trs.sdk;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ClientTest {
    public static void main(String[] args) throws Exception {
        testHealthSubmitQuerySyncReplay();
        testValidationError();
        testTimeoutConnectionError();
        System.out.println("All trs-sdk-java tests passed.");
    }

    private static void testHealthSubmitQuerySyncReplay() throws Exception {
        TestNode node = new TestNode(0);
        try {
            TRSClient client = new TRSClient(node.baseUrl(), Duration.ofSeconds(2));
            HealthStatus health = client.health();
            assertEquals("ok", health.status(), "health.status");

            client.submit(record("g1", "Observation", Map.of("subject", "boot", "value", 1)));
            List<Map<String, Object>> rows = client.query(Map.of("type", "Observation"));
            assertEquals(1, rows.size(), "query size");

            var sync = client.sync(rows);
            assertEquals(1, sync.acceptedCount(), "sync accepted_count");

            Map<String, Object> replay = client.replay();
            assertTrue(replay.containsKey("coordination"), "replay has coordination");
        } finally {
            node.stop();
        }
    }

    private static void testValidationError() throws Exception {
        TestNode node = new TestNode(0);
        try {
            TRSClient client = new TRSClient(node.baseUrl(), Duration.ofSeconds(2));
            try {
                client.submit(record("bad", "Observation", Map.of()));
                throw new AssertionError("expected TRSValidationError");
            } catch (TRSValidationError expected) {
                assertTrue(true, "validation error observed");
            }
        } finally {
            node.stop();
        }
    }

    private static void testTimeoutConnectionError() {
        TestNode node = null;
        try {
            node = new TestNode(250);
            TRSClient client = new TRSClient(node.baseUrl(), Duration.ofMillis(30));
            try {
                client.health();
                throw new AssertionError("expected TRSConnectionError");
            } catch (TRSConnectionError expected) {
                assertTrue(true, "connection error observed");
            }
        } catch (Exception ex) {
            throw new RuntimeException(ex);
        } finally {
            if (node != null) {
                node.stop();
            }
        }
    }

    private static Map<String, Object> record(String id, String type, Map<String, Object> payload) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("type", type);
        out.put("author", "tester");
        out.put("timestamp", "2026-08-04T10:00:00+00:00");
        out.put("schema", switch (type) {
            case "Observation" -> "trs.observation.v1";
            case "Intention" -> "trs.intention.v1";
            case "Commitment" -> "trs.commitment.v1";
            default -> "unknown";
        });
        out.put("payload", payload);
        out.put("causes", List.of());
        out.put("authorization", List.of());
        out.put("signature", "sig:" + id);
        return out;
    }

    private static void assertEquals(Object expected, Object actual, String label) {
        if ((expected == null && actual != null) || (expected != null && !expected.equals(actual))) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    private static void assertTrue(boolean value, String label) {
        if (!value) {
            throw new AssertionError(label);
        }
    }

    private static final class TestNode {
        private final HttpServer server;
        private final List<Map<String, Object>> records = new ArrayList<>();
        private final long delayMillis;

        private TestNode(long delayMillis) throws IOException {
            this.delayMillis = delayMillis;
            this.server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            this.server.createContext("/health", this::handleHealth);
            this.server.createContext("/submit", this::handleSubmit);
            this.server.createContext("/query", this::handleQuery);
            this.server.createContext("/sync", this::handleSync);
            this.server.createContext("/replay", this::handleReplay);
            this.server.start();
        }

        private String baseUrl() {
            return "http://127.0.0.1:" + server.getAddress().getPort();
        }

        private void stop() {
            server.stop(0);
        }

        private void maybeDelay() {
            if (delayMillis <= 0) {
                return;
            }
            try {
                Thread.sleep(delayMillis);
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
            }
        }

        private void handleHealth(HttpExchange exchange) throws IOException {
            maybeDelay();
            write(exchange, 200, "{\"status\":\"ok\",\"runtime\":\"1.0.0\",\"node\":\"0.1.0\"}");
        }

        @SuppressWarnings("unchecked")
        private void handleSubmit(HttpExchange exchange) throws IOException {
            maybeDelay();
            String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            Object parsed = Jsons.parse(body);
            Map<String, Object> root = (Map<String, Object>) parsed;
            Map<String, Object> record = (Map<String, Object>) root.get("record");
            Map<String, Object> payload = (Map<String, Object>) record.get("payload");

            boolean valid = payload.containsKey("subject") || payload.containsKey("goal") || payload.containsKey("action");
            if (!valid) {
                write(
                        exchange,
                        200,
                        "{\"accepted\":false,\"record_id\":\""
                                + record.get("id")
                                + "\",\"errors\":[\"5.3 Payload Shape\"]}");
                return;
            }
            records.add(record);
            write(
                    exchange,
                    200,
                    "{\"accepted\":true,\"record_id\":\"" + record.get("id") + "\",\"errors\":[]}");
        }

        private void handleQuery(HttpExchange exchange) throws IOException {
            maybeDelay();
            String rows = Jsons.stringify(Map.of("records", records));
            write(exchange, 200, rows);
        }

        private void handleSync(HttpExchange exchange) throws IOException {
            maybeDelay();
            write(
                    exchange,
                    200,
                    "{\"accepted_count\":1,\"rejected_count\":0,\"appended_ids\":[\"g1\"],\"rejected_errors\":[]}");
        }

        private void handleReplay(HttpExchange exchange) throws IOException {
            maybeDelay();
            write(exchange, 200, "{\"coordination\":{\"unresolved_intentions\":[]}}");
        }

        private void write(HttpExchange exchange, int code, String json) throws IOException {
            byte[] payload = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(code, payload.length);
            try (OutputStream out = exchange.getResponseBody()) {
                out.write(payload);
            }
        }
    }
}
