# CYCLE-0010 — TerraNode Program 8 Public Submission Boundary

## Status

Closed — TRS survives.

## Depends on

- CYCLE-0009 complete.

## New question

Can untrusted writers be safely admitted using edge controls without contaminating TRS core?

## Evidence targets

- Rate/abuse controls at adapter boundary.
- Runtime remains deterministic append+verify engine.

## Evidence run

- `evidence/test_runs/2026-08-03T125659Z_terranode_program4_program9.log`
- `terranode/tests/test_program8_public_submission_boundary.py`

## Amendment trigger

If anti-abuse protections require changing core TRS verification semantics.
