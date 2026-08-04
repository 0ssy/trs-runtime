package dev.trs.sdk;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

final class Jsons {
    private Jsons() {}

    static Object parse(String json) {
        return new Parser(json).parse();
    }

    static String stringify(Object value) {
        if (value == null) {
            return "null";
        }
        if (value instanceof String s) {
            return "\"" + escape(s) + "\"";
        }
        if (value instanceof Boolean || value instanceof Number) {
            return value.toString();
        }
        if (value instanceof Map<?, ?> map) {
            StringBuilder builder = new StringBuilder("{");
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) {
                    builder.append(",");
                }
                first = false;
                builder.append(stringify(String.valueOf(entry.getKey())));
                builder.append(":");
                builder.append(stringify(entry.getValue()));
            }
            builder.append("}");
            return builder.toString();
        }
        if (value instanceof List<?> list) {
            StringBuilder builder = new StringBuilder("[");
            for (int i = 0; i < list.size(); i++) {
                if (i > 0) {
                    builder.append(",");
                }
                builder.append(stringify(list.get(i)));
            }
            builder.append("]");
            return builder.toString();
        }
        throw new TRSProtocolError("unsupported JSON type: " + value.getClass().getName());
    }

    private static String escape(String value) {
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    private static final class Parser {
        private final String source;
        private int index = 0;

        private Parser(String source) {
            this.source = source;
        }

        private Object parse() {
            skipWs();
            Object value = parseValue();
            skipWs();
            if (index != source.length()) {
                throw new TRSProtocolError("unexpected token at index " + index);
            }
            return value;
        }

        private Object parseValue() {
            skipWs();
            if (index >= source.length()) {
                throw new TRSProtocolError("unexpected end of JSON");
            }
            char c = source.charAt(index);
            if (c == '{') return parseObject();
            if (c == '[') return parseArray();
            if (c == '"') return parseString();
            if (c == 't') return consumeKeyword("true", Boolean.TRUE);
            if (c == 'f') return consumeKeyword("false", Boolean.FALSE);
            if (c == 'n') return consumeKeyword("null", null);
            return parseNumber();
        }

        private Map<String, Object> parseObject() {
            expect('{');
            Map<String, Object> out = new LinkedHashMap<>();
            skipWs();
            if (peek('}')) {
                expect('}');
                return out;
            }
            while (true) {
                String key = parseString();
                skipWs();
                expect(':');
                skipWs();
                out.put(key, parseValue());
                skipWs();
                if (peek('}')) {
                    expect('}');
                    return out;
                }
                expect(',');
                skipWs();
            }
        }

        private List<Object> parseArray() {
            expect('[');
            List<Object> out = new ArrayList<>();
            skipWs();
            if (peek(']')) {
                expect(']');
                return out;
            }
            while (true) {
                out.add(parseValue());
                skipWs();
                if (peek(']')) {
                    expect(']');
                    return out;
                }
                expect(',');
                skipWs();
            }
        }

        private String parseString() {
            expect('"');
            StringBuilder out = new StringBuilder();
            while (index < source.length()) {
                char c = source.charAt(index++);
                if (c == '"') {
                    return out.toString();
                }
                if (c == '\\') {
                    if (index >= source.length()) {
                        throw new TRSProtocolError("invalid escape");
                    }
                    char e = source.charAt(index++);
                    if (e == '"' || e == '\\' || e == '/') out.append(e);
                    else if (e == 'b') out.append('\b');
                    else if (e == 'f') out.append('\f');
                    else if (e == 'n') out.append('\n');
                    else if (e == 'r') out.append('\r');
                    else if (e == 't') out.append('\t');
                    else throw new TRSProtocolError("unsupported escape: \\" + e);
                } else {
                    out.append(c);
                }
            }
            throw new TRSProtocolError("unterminated string");
        }

        private Object consumeKeyword(String keyword, Object value) {
            if (source.startsWith(keyword, index)) {
                index += keyword.length();
                return value;
            }
            throw new TRSProtocolError("invalid token at index " + index);
        }

        private Number parseNumber() {
            int start = index;
            while (index < source.length()) {
                char c = source.charAt(index);
                if ((c >= '0' && c <= '9') || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E') {
                    index++;
                } else {
                    break;
                }
            }
            String raw = source.substring(start, index);
            try {
                if (raw.contains(".") || raw.contains("e") || raw.contains("E")) {
                    return Double.parseDouble(raw);
                }
                return Long.parseLong(raw);
            } catch (NumberFormatException ex) {
                throw new TRSProtocolError("invalid number: " + raw);
            }
        }

        private boolean peek(char expected) {
            return index < source.length() && source.charAt(index) == expected;
        }

        private void expect(char expected) {
            if (index >= source.length() || source.charAt(index) != expected) {
                throw new TRSProtocolError("expected '" + expected + "' at index " + index);
            }
            index++;
        }

        private void skipWs() {
            while (index < source.length()) {
                char c = source.charAt(index);
                if (c == ' ' || c == '\n' || c == '\r' || c == '\t') {
                    index++;
                    continue;
                }
                break;
            }
        }
    }
}

