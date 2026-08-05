# TRS Network Protocol (TRS-NET-1)

Base operations:

- `GET /health`
- `GET /record/{id}`
- `POST /submit`
- `POST /query`
- `POST /sync`
- `POST /replay`

Canonical request/response schemas are aligned with `trs-openapi/openapi.yaml`.

## Request contracts

- `POST /submit`
  - body: `{ "record": <RecordEnvelope> }`
- `POST /query`
  - body: `{ "query": <object> }`
- `POST /sync`
  - body: `{ "records": [<RecordEnvelope>...] }`
- `POST /replay`
  - body: `{}` (empty object)

## Response contracts

- `GET /health` -> `{ "status": "ok", "runtime": "...", "node": "..." }`
- `GET /record/{id}` -> `<RecordEnvelope>` or not-found error
- `POST /submit` -> `{ "accepted": bool, "record_id": "...", "errors": [...] }`
- `POST /query` -> `{ "records": [<RecordEnvelope>...] }`
- `POST /sync` -> `{ "accepted_count": int, "rejected_count": int, "appended_ids": [...], "rejected_errors": [[...], ...] }`
- `POST /replay` -> replay snapshot object

## Error envelope

```json
{
  "detail": "human readable error",
  "code": "optional_machine_code",
  "request_id": "optional-request-id"
}
```

Status codes:

- `200`: success
- `400`: malformed/invalid business input
- `404`: unknown record id
- `413`: request too large
- `422`: schema/shape validation failure
- `504`: request timeout
