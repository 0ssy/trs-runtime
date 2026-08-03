# Program 7 — Capability Security

## Status

Complete (TRS survives).

## Research question

Do delegation, scope, expiry, and forged-authority defenses hold under TerraNode attack execution?

## Dependency

Requires Program 6 semantic-interoperability baseline.

## Gate

- Attack suite covers delegation misuse, forgery, transitivity abuse, and supersession.
- All attacks are explicitly visible and blocked at verification boundaries.

## Executable evidence

- `terranode/tests/test_program7_capability_security.py`
- `evidence/test_runs/2026-08-03T125659Z_terranode_program4_program9.log`
