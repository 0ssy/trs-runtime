# TerraNode Program 1 Evidence

## Test commands

Run from repository root:

```bash
python -m unittest -v terranode.tests.test_policy
python -m unittest -v terranode.tests.test_adapter
python -m unittest -v terranode.tests.test_program1
```

## Expected outputs

- Policy test validates deterministic pro-rata split.
- Adapter test validates intention submission, conflict discovery, allocation writes, and closure.
- Program test validates full demo replay path and final totals.
