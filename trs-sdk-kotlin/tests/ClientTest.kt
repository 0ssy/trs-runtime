package dev.trs.sdk

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.time.Duration

fun main() {
    testHealthSubmitQuerySyncReplay()
    testValidationError()
    testTimeoutConnectionError()
    println("All trs-sdk-kotlin tests passed.")
}

private fun testHealthSubmitQuerySyncReplay() {
    val server = TestServer(delayMs = 0)
    try {
        val client = TrsClient(server.baseUrl, Duration.ofSeconds(2))
        val health = client.health()
        checkEquals("ok", health.status, "health.status")

        client.submit(
            mapOf(
                "id" to "g1",
                "type" to "Observation",
                "payload" to mapOf("subject" to "boot", "value" to 1),
            )
        )

        val rows = client.query(emptyMap())
        checkEquals(1, rows.size, "query size")
        val sync = client.sync(rows)
        checkEquals(1, sync.acceptedCount, "sync accepted_count")
        val replay = client.replay()
        checkTrue(replay.containsKey("coordination"), "replay contains coordination")
    } finally {
        server.close()
    }
}

private fun testValidationError() {
    val server = TestServer(delayMs = 0)
    try {
        val client = TrsClient(server.baseUrl, Duration.ofSeconds(2))
        try {
            client.submit(
                mapOf(
                    "id" to "bad",
                    "type" to "Observation",
                    "payload" to emptyMap<String, Any?>(),
                )
            )
            throw IllegalStateException("expected TrsValidationError")
        } catch (_: TrsValidationError) {
        }
    } finally {
        server.close()
    }
}

private fun testTimeoutConnectionError() {
    val server = TestServer(delayMs = 250)
    try {
        val client = TrsClient(server.baseUrl, Duration.ofMillis(20))
        try {
            client.health()
            throw IllegalStateException("expected TrsConnectionError")
        } catch (_: TrsConnectionError) {
        }
    } finally {
        server.close()
    }
}

private fun checkEquals(expected: Any, actual: Any, label: String) {
    if (expected != actual) {
        throw IllegalStateException("$label expected=$expected actual=$actual")
    }
}

private fun checkTrue(value: Boolean, label: String) {
    if (!value) {
        throw IllegalStateException("$label expected true")
    }
}

private class TestServer(private val delayMs: Long) {
    private val server: HttpServer = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
    private val records = mutableListOf<Map<String, Any?>>()

    val baseUrl: String

    init {
        server.createContext("/health") { exchange ->
            maybeDelay()
            respond(exchange, """{"status":"ok","runtime":"1.0.0","node":"0.1.0"}""")
        }
        server.createContext("/submit") { exchange ->
            maybeDelay()
            val body = exchange.requestBody.bufferedReader().use { it.readText().ifBlank { "{}" } }
            val root = Jsons.parse(body) as Map<*, *>
            val record = root["record"] as Map<*, *>
            val payload = record["payload"] as? Map<*, *> ?: emptyMap<String, Any?>()
            val valid = payload.containsKey("subject") || payload.containsKey("goal") || payload.containsKey("action")
            val id = record["id"]?.toString() ?: ""
            if (!valid) {
                respond(exchange, """{"accepted":false,"record_id":"$id","errors":["5.3 Payload Shape"]}""")
            } else {
                @Suppress("UNCHECKED_CAST")
                records.add(record as Map<String, Any?>)
                respond(exchange, """{"accepted":true,"record_id":"$id","errors":[]}""")
            }
        }
        server.createContext("/query") { exchange ->
            maybeDelay()
            respond(exchange, Jsons.stringify(mapOf("records" to records)))
        }
        server.createContext("/sync") { exchange ->
            maybeDelay()
            respond(exchange, """{"accepted_count":1,"rejected_count":0,"appended_ids":["g1"],"rejected_errors":[]}""")
        }
        server.createContext("/replay") { exchange ->
            maybeDelay()
            respond(exchange, """{"coordination":{"unresolved_intentions":[]}}""")
        }
        server.start()
        baseUrl = "http://127.0.0.1:${server.address.port}"
    }

    fun close() {
        server.stop(0)
    }

    private fun maybeDelay() {
        if (delayMs > 0) {
            Thread.sleep(delayMs)
        }
    }

    private fun respond(exchange: com.sun.net.httpserver.HttpExchange, body: String) {
        val payload = body.toByteArray(Charsets.UTF_8)
        exchange.responseHeaders.add("Content-Type", "application/json")
        exchange.sendResponseHeaders(200, payload.size.toLong())
        exchange.responseBody.use { out ->
            out.write(payload)
        }
    }
}

