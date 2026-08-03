# Program 3 — Policy Independence

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
