# Conformance Runner Spec

## Inputs

A runner accepts:

1. Vector category (`valid`, `invalid`, `replay`, `authorization`)
2. Vector file path
3. Optional implementation metadata:
   - `implementation_name`
   - `implementation_version`

## Processing contract

For each vector:

1. Start from empty store.
2. Ingest records in listed order.
3. For `valid` and `invalid` vectors:
   - verify each record at ingest time.
4. For `replay` vectors:
   - run replay after ingesting all records.
5. For `authorization` vectors:
   - capture authorization-path evidence on target records.

## Output JSON shape

```json
{
  "implementation_name": "example-runtime",
  "implementation_version": "0.1.0",
  "vector_id": "valid-minimal-genesis",
  "status": "pass",
  "details": {
    "verified_records": ["g1"],
    "failed_records": [],
    "errors": []
  }
}
```

Required fields:

- `vector_id` (string)
- `status` (`pass` or `fail`)
- `details` (object)

## Matching policy

- For pass/fail, exact match with expected status is required.
- For rule evidence strings, expected substrings must appear in produced evidence.
- Implementations may include extra metadata fields, but must preserve required fields.
