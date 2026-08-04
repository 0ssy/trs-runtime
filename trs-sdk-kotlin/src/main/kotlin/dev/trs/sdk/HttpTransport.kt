package dev.trs.sdk

import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration

internal class HttpTransport(baseUrl: String, timeout: Duration) {
    private val baseUrl: String = baseUrl.trimEnd('/')
    private val timeout: Duration = timeout
    private val client: HttpClient = HttpClient.newBuilder().connectTimeout(timeout).build()

    fun get(path: String): Any? = send("GET", path, null)

    fun post(path: String, payload: Any?): Any? = send("POST", path, payload)

    private fun send(method: String, path: String, payload: Any?): Any? {
        val requestBuilder = HttpRequest.newBuilder(URI.create(baseUrl + path))
            .timeout(timeout)
            .header("Accept", "application/json")
        if (method == "POST") {
            requestBuilder
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(Jsons.stringify(payload)))
        } else {
            requestBuilder.GET()
        }
        val response = try {
            client.send(requestBuilder.build(), HttpResponse.BodyHandlers.ofString())
        } catch (ex: Exception) {
            throw TrsConnectionError(ex.message ?: "connection error", ex)
        }
        val body = response.body().ifBlank { "{}" }
        val parsed = try {
            Jsons.parse(body)
        } catch (ex: Exception) {
            throw TrsProtocolError("invalid JSON response from trs-node")
        }
        if (response.statusCode() in 200..299) {
            return parsed
        }
        val message = extractErrorMessage(parsed, response.statusCode())
        if (response.statusCode() in 400..499) {
            throw TrsValidationError(message, emptyList())
        }
        throw TrsServerError(message)
    }

    private fun extractErrorMessage(payload: Any?, statusCode: Int): String {
        if (payload is Map<*, *>) {
            val detail = payload["detail"] as? String
            if (!detail.isNullOrBlank()) {
                return detail
            }
            val error = payload["error"] as? String
            if (!error.isNullOrBlank()) {
                return error
            }
        }
        return "http $statusCode"
    }
}

