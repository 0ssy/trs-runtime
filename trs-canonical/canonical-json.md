# Canonical JSON (TRS-CANONICAL-1)

This profile defines a single byte representation for a TRS record.

## Record scope

Canonicalization applies to the full record envelope:

- `id`
- `type`
- `author`
- `timestamp`
- `schema`
- `payload`
- `causes`
- `authorization`
- `signature`
- `subject`

No field may be inferred from payload.

## Encoding

- UTF-8 bytes only.
- Object keys and string values MUST be Unicode scalar values.
- Newlines in generated canonical JSON are forbidden.

## Object key ordering

- Sort object keys lexicographically by Unicode code point.
- Apply recursively to nested objects in `payload`.

## Arrays

- Preserve array order exactly as submitted.
- No array sorting is allowed.

## Numbers

- Finite JSON numbers only (no NaN/Infinity).
- No leading plus signs.
- No unnecessary leading zeros.
- No trailing decimal point.
- Use shortest round-trippable decimal form.

## Whitespace

- No extra whitespace.
- Canonical separators:
  - item separator: `,`
  - key separator: `:`

## Timestamp form

- RFC 3339 / ISO-8601 string with explicit offset.
- Implementations should normalize UTC to `Z` or `+00:00` consistently per implementation profile.

## Canonical output

The result is a single UTF-8 byte string used by hashing/signing procedures.
