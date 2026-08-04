package dev.trs.sdk

import java.time.Duration

class TrsClient(baseUrl: String, timeout: Duration = Duration.ofSeconds(5)) {
    private val transport = HttpTransport(baseUrl, timeout)

    fun health(): HealthStatus {
        val payload = asMap(transport.get("/health"), "health response")
        return HealthStatus(
            status = payload["status"]?.toString() ?: "",
            runtime = payload["runtime"]?.toString() ?: "",
            node = payload["node"]?.toString() ?: "",
        )
    }

    fun submit(record: Map<String, Any?>): SubmitResult {
        val payload = asMap(transport.post("/submit", mapOf("record" to record)), "submit response")
        val accepted = payload["accepted"] as? Boolean ?: false
        val recordId = payload["record_id"]?.toString() ?: ""
        val errors = asStringList(payload["errors"], "errors")
        val out = SubmitResult(accepted = accepted, recordId = recordId, errors = errors)
        if (!out.accepted) {
            throw TrsValidationError("record rejected by verifier", out.errors)
        }
        return out
    }

    fun query(expr: Map<String, Any?>): List<Map<String, Any?>> {
        val payload = asMap(transport.post("/query", mapOf("query" to expr)), "query response")
        val records = payload["records"] as? List<*>
            ?: throw TrsProtocolError("records must be an array")
        return records.map { asMap(it, "record") }
    }

    fun sync(records: List<Map<String, Any?>>): SyncResult {
        val payload = asMap(transport.post("/sync", mapOf("records" to records)), "sync response")
        val acceptedCount = (payload["accepted_count"] as? Number)?.toInt() ?: 0
        val rejectedCount = (payload["rejected_count"] as? Number)?.toInt() ?: 0
        val appendedIds = asStringList(payload["appended_ids"], "appended_ids")
        val rejectedErrors = asStringListList(payload["rejected_errors"], "rejected_errors")
        return SyncResult(
            acceptedCount = acceptedCount,
            rejectedCount = rejectedCount,
            appendedIds = appendedIds,
            rejectedErrors = rejectedErrors,
        )
    }

    fun replay(): Map<String, Any?> {
        return asMap(transport.post("/replay", emptyMap<String, Any?>()), "replay response")
    }

    @Suppress("UNCHECKED_CAST")
    private fun asMap(value: Any?, label: String): Map<String, Any?> {
        if (value is Map<*, *>) {
            return value as Map<String, Any?>
        }
        throw TrsProtocolError("$label must be an object")
    }

    private fun asStringList(value: Any?, label: String): List<String> {
        val list = value as? List<*> ?: throw TrsProtocolError("$label must be an array")
        return list.map { it.toString() }
    }

    private fun asStringListList(value: Any?, label: String): List<List<String>> {
        val list = value as? List<*> ?: throw TrsProtocolError("$label must be an array")
        return list.map { item -> asStringList(item, "$label entry") }
    }
}

