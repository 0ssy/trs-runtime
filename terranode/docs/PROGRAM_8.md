# Program 8 — Public Submission Boundary

## Research question

Can untrusted external writers submit safely using adapter and edge controls while TRS stays unchanged?

## Dependency

Requires Program 7 capability-security baseline.

## Gate

- Spam/abuse controls implemented outside TRS runtime.
- Malformed payloads and quotas are enforced at submission boundary.
- Runtime remains a deterministic verifier and append-only store.
