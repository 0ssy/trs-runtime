# TerraNode Research Roadmap — Programs 2 to 9

This roadmap enforces strict dependency order. Each program introduces exactly one new research question and keeps TRS runtime frozen.

## Dependency chain

P2 -> P3 -> P4 -> P5 -> P6 -> P7 -> P8 -> P9

## Rule for every program

Each program must end in exactly one of:

1. TRS survives, or
2. Reproducible contradiction that justifies a TRS amendment candidate.

## Program stack

### Program 2 — Distributed Validation

- New question: does coordination hold under partition and reconnect (§4.3 pressure).
- Depends on: Program 1 baseline.
- Key artifact: `terranode/tests/test_program2_distributed.py`.
- Status: Complete (TRS survives).

### Program 3 — Policy Independence

- New question: can policies vary while adapter/runtime remain unchanged.
- Depends on: Program 2 convergence baseline.
- Key artifact: `terranode/tests/test_program3_policy_independence.py`.
- Status: Complete (TRS survives).

### Program 4 — Trust-Weighted Coordination

- New question: can trust/reputation weighting stay policy-layer only.
- Depends on: Program 3 policy abstraction stability.
- Status: Complete (TRS survives).

### Program 5 — Multi-Authority Coordination

- New question: can overlapping authorities coordinate safely.
- Depends on: Program 4 trust-weighted baseline.
- Status: Complete (TRS survives).

### Program 6 — Semantic Interoperability

- New question: can differing local semantics interoperate via explicit mapping commitments.
- Depends on: Program 5 authority baseline.
- Status: Complete (TRS survives).

### Program 7 — Capability Security

- New question: does delegation and scoped authority survive adversarial pressure in TerraNode flows.
- Depends on: Program 6 semantic baseline.
- Status: Complete (TRS survives).

### Program 8 — Public Submission Boundary

- New question: can untrusted writers submit safely without pushing concerns into TRS core.
- Depends on: Program 7 capability hardening.
- Status: Complete (TRS survives).

### Program 9 — Human Systems

- New question: can offline human channels operate while preserving history and replay.
- Depends on: Programs 2–8 backend validity.
- Status: Complete (TRS survives).

## Freeze boundary

- `runtime/` remains frozen unless contradiction is reproducible.
- Adapter/edge/policy/human interfaces can evolve.

## Pre-pilot extension

Before any real pilot, execute the mandatory pre-pilot stack:

- `terranode/docs/PRE_PILOT_STACK_9_5_TO_9_11.md`
