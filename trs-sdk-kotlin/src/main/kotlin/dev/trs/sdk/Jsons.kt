package dev.trs.sdk

object Jsons {
    fun parse(json: String): Any? = Parser(json).parse()

    fun stringify(value: Any?): String {
        return when (value) {
            null -> "null"
            is String -> "\"" + escape(value) + "\""
            is Boolean, is Number -> value.toString()
            is Map<*, *> -> value.entries.joinToString(prefix = "{", postfix = "}") { entry ->
                stringify(entry.key.toString()) + ":" + stringify(entry.value)
            }
            is List<*> -> value.joinToString(prefix = "[", postfix = "]") { item -> stringify(item) }
            else -> throw TrsProtocolError("unsupported JSON type: ${value::class.java.name}")
        }
    }

    private fun escape(value: String): String {
        return value
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
    }

    private class Parser(private val source: String) {
        private var index: Int = 0

        fun parse(): Any? {
            skipWs()
            val value = parseValue()
            skipWs()
            if (index != source.length) {
                throw TrsProtocolError("unexpected token at index $index")
            }
            return value
        }

        private fun parseValue(): Any? {
            skipWs()
            if (index >= source.length) {
                throw TrsProtocolError("unexpected end of JSON")
            }
            return when (val c = source[index]) {
                '{' -> parseObject()
                '[' -> parseArray()
                '"' -> parseString()
                't' -> consumeKeyword("true", true)
                'f' -> consumeKeyword("false", false)
                'n' -> consumeKeyword("null", null)
                else -> if (c == '-' || c.isDigit()) parseNumber() else throw TrsProtocolError("invalid token at index $index")
            }
        }

        private fun parseObject(): Map<String, Any?> {
            expect('{')
            val out = linkedMapOf<String, Any?>()
            skipWs()
            if (peek('}')) {
                expect('}')
                return out
            }
            while (true) {
                val key = parseString()
                skipWs()
                expect(':')
                skipWs()
                out[key] = parseValue()
                skipWs()
                if (peek('}')) {
                    expect('}')
                    return out
                }
                expect(',')
                skipWs()
            }
        }

        private fun parseArray(): List<Any?> {
            expect('[')
            val out = mutableListOf<Any?>()
            skipWs()
            if (peek(']')) {
                expect(']')
                return out
            }
            while (true) {
                out.add(parseValue())
                skipWs()
                if (peek(']')) {
                    expect(']')
                    return out
                }
                expect(',')
                skipWs()
            }
        }

        private fun parseString(): String {
            expect('"')
            val out = StringBuilder()
            while (index < source.length) {
                val c = source[index++]
                if (c == '"') {
                    return out.toString()
                }
                if (c == '\\') {
                    if (index >= source.length) {
                        throw TrsProtocolError("invalid escape")
                    }
                    val e = source[index++]
                    when (e) {
                        '"', '\\', '/' -> out.append(e)
                        'b' -> out.append('\b')
                        'f' -> out.append('\u000c')
                        'n' -> out.append('\n')
                        'r' -> out.append('\r')
                        't' -> out.append('\t')
                        else -> throw TrsProtocolError("unsupported escape: \\$e")
                    }
                } else {
                    out.append(c)
                }
            }
            throw TrsProtocolError("unterminated string")
        }

        private fun consumeKeyword(keyword: String, value: Any?): Any? {
            if (source.startsWith(keyword, index)) {
                index += keyword.length
                return value
            }
            throw TrsProtocolError("invalid token at index $index")
        }

        private fun parseNumber(): Number {
            val start = index
            while (index < source.length) {
                val c = source[index]
                if (c.isDigit() || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E') {
                    index++
                } else {
                    break
                }
            }
            val raw = source.substring(start, index)
            return try {
                if (raw.contains('.') || raw.contains('e') || raw.contains('E')) raw.toDouble() else raw.toLong()
            } catch (ex: NumberFormatException) {
                throw TrsProtocolError("invalid number: $raw")
            }
        }

        private fun peek(expected: Char): Boolean = index < source.length && source[index] == expected

        private fun expect(expected: Char) {
            if (index >= source.length || source[index] != expected) {
                throw TrsProtocolError("expected '$expected' at index $index")
            }
            index++
        }

        private fun skipWs() {
            while (index < source.length && source[index].isWhitespace()) {
                index++
            }
        }
    }
}

