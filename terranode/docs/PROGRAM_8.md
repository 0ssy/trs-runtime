# Program 8 — Public Submission Boundary

## Status

Complete (TRS survives).

## Research question

Can untrusted external writers submit safely using adapter and edge controls while TRS stays unchanged?

## Dependency

Requires Program 7 capability-security baseline.

## Gate

- Spam/abuse controls implemented outside TRS runtime.
- Malformed payloads and quotas are enforced at submission boundary.
- Runtime remains a deterministic verifier and append-only store.

## Executable evidence

- `terranode/tests/test_program8_public_submission_boundary.py`
- `evidence/test_runs/2026-08-03T125659Z_terranode_program4_program9.log`
