# Program 4 — Trust-Weighted Coordination

## Status

Complete (TRS survives).

## Research question

Can identity confidence and reputation decay influence allocation strictly in policy space?

## Dependency

Requires Program 3 policy-independence baseline.

## Gate

- Weighting logic lives outside TRS runtime.
- Runtime records remain immutable and payload-independent.
- Trust weighting is reproducible via replay plus policy input.

## Executable evidence

- `terranode/tests/test_program4_trust_weighted.py`
- `evidence/test_runs/2026-08-03T125659Z_terranode_program4_program9.log`
