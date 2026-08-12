# TRS Deployment Guidance

## Core deployment rule

Run TRS **alongside** the application as a coordination/provenance layer.  
Do **not** put TRS verification/storage in the synchronous user request path for primary app data writes.

## Why

- TRS must stay domain-neutral and append-only.
- Application latency/availability budgets should not be coupled to provenance ingestion.
- Boundary controls (quotas, authN/authZ, abuse checks) belong at the app/edge layer.

## Recommended topology

1. Application accepts user/API action.
2. Application commits its own domain state in its native store.
3. Application emits a TRS envelope asynchronously (queue/outbox/worker).
4. TRS runtime verifies and appends immutable records.
5. Replay/query/explain surfaces consume TRS records for audit, conflict, and authority traceability.

## Operational notes

- If TRS ingest is delayed, app operation continues; provenance catches up.
- If TRS rejects a record, treat it as a coordination integrity signal, not a request-path crash condition.
- Keep retry/idempotency at adapter/outbox level; keep TRS runtime deterministic.

