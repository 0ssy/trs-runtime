# TerraNode Program 1 Evidence

## Test commands

Run from repository root:

```bash
python -m unittest -v terranode.tests.test_policy
python -m unittest -v terranode.tests.test_adapter
python -m unittest -v terranode.tests.test_program1
python -m unittest -v terranode.tests.test_program2_distributed
python -m unittest -v terranode.tests.test_program3_policy_independence
```

## Expected outputs

- Policy test validates deterministic pro-rata split.
- Adapter test validates intention submission, conflict discovery, allocation writes, and closure.
- Program test validates full demo replay path and final totals.
- Program 2 test validates partition/reconnect convergence and conflict visibility.
- Program 3 test validates policy substitution with unchanged adapter flow.
