package dev.trs.sdk

open class TrsException(message: String, cause: Throwable? = null) : RuntimeException(message, cause)

class TrsConnectionError(message: String, cause: Throwable? = null) : TrsException(message, cause)

class TrsValidationError(message: String, val errors: List<String>) : TrsException(message)

class TrsServerError(message: String) : TrsException(message)

class TrsProtocolError(message: String) : TrsException(message)

