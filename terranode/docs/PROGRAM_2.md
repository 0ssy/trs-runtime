# Program 2 — Distributed Validation

## Research question

Does TerraNode coordination remain valid when nodes allocate under partition and later reconnect?

## Dependency

Requires Program 1 consumer validation complete.

## Gate

- Reconnect converges record inventories.
- No lost records.
- Replay succeeds after convergence.
- Conflicts become visible post-reconnect.
- No TRS runtime modifications are required.

## Executable evidence

- `terranode/tests/test_program2_distributed.py`
