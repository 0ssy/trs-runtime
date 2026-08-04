package dev.trs.sdk;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;

final class HTTPTransport {
    private final String baseUrl;
    private final HttpClient httpClient;
    private final Duration timeout;

    HTTPTransport(String baseUrl, Duration timeout) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.timeout = timeout;
        this.httpClient = HttpClient.newBuilder().connectTimeout(timeout).build();
    }

    Object get(String path) {
        return send("GET", path, null);
    }

    Object post(String path, Object body) {
        return send("POST", path, body);
    }

    private Object send(String method, String path, Object body) {
        String rawBody = body == null ? "" : Jsons.stringify(body);
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(baseUrl + path))
                .timeout(timeout)
                .header("Accept", "application/json");
        if ("POST".equals(method)) {
            builder = builder
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(rawBody));
        } else {
            builder = builder.GET();
        }
        HttpResponse<String> response;
        try {
            response = httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofString());
        } catch (IOException | InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new TRSConnectionError(ex.getMessage(), ex);
        }
        Object payload;
        try {
            payload = response.body().isEmpty() ? Map.of() : Jsons.parse(response.body());
        } catch (RuntimeException ex) {
            throw new TRSProtocolError("invalid JSON response from trs-node");
        }

        if (response.statusCode() >= 200 && response.statusCode() < 300) {
            return payload;
        }
        String message = extractErrorMessage(payload, response.statusCode());
        if (response.statusCode() >= 400 && response.statusCode() < 500) {
            throw new TRSValidationError(message, List.of());
        }
        throw new TRSServerError(message);
    }

    private String extractErrorMessage(Object payload, int statusCode) {
        if (payload instanceof Map<?, ?> map) {
            Object detail = map.get("detail");
            if (detail instanceof String s && !s.isBlank()) {
                return s;
            }
            Object error = map.get("error");
            if (error instanceof String s && !s.isBlank()) {
                return s;
            }
        }
        return "http " + statusCode;
    }
}

