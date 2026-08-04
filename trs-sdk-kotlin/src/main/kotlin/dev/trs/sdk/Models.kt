package dev.trs.sdk

data class HealthStatus(val status: String, val runtime: String, val node: String)

data class SubmitResult(val accepted: Boolean, val recordId: String, val errors: List<String>)

data class SyncResult(
    val acceptedCount: Int,
    val rejectedCount: Int,
    val appendedIds: List<String>,
    val rejectedErrors: List<List<String>>,
)

