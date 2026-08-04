# Program 3 — Policy Independence

## Status

Complete (TRS survives).

## Research question

Is `AllocationPolicy` a stable abstraction that allows policy replacement without adapter/runtime rewrites?

## Dependency

Requires Program 2 distributed baseline complete.

## Gate

- Multiple policy implementations run through the same adapter flow.
- Runtime remains untouched.
- Adapter call pattern remains unchanged.

## Executable evidence

- `terranode/tests/test_program3_policy_independence.py`
- `evidence/test_runs/2026-08-03T125317Z_terranode_program2_program3.log`
- `evidence/test_runs/2026-08-04T071409Z_terranode_full_suite.log`

## Outcome

- ProRata, Priority, Weighted, Auction, Lottery, EmergencyOverride, and FairShare policies all run through the same adapter flow.
- Adapter surface remains unchanged across policy substitutions.
- No TRS runtime (`runtime/`) modification was required to satisfy Program 3 gates.
