# ATTACK-011 — Malformed Envelope Fuzz

Goal: Crash or bypass validation through malformed envelopes and random payload shapes.  
Hypothesis: Adapter or verifier may throw unhandled exceptions or accept malformed structures.

Expected: Fail safely (clean rejection), no runtime crash.

Actual:
- Status: BLOCKED
- Evidence:
  - `tests/test_fuzz_malformed_inputs.py::test_malformed_envelope_never_crashes_adapter`
  - `tests/test_fuzz_malformed_inputs.py::test_random_payload_for_declared_primitive_never_crashes_verifier`

Affected Rules:
- 5.3 Payload Shape
- 6.1 Authorization Traceability (input path shape hardening)

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: Yes (adapter envelope validation hardened)  
Tests added?: Yes (`tests/test_fuzz_malformed_inputs.py`)
