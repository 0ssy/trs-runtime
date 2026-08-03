# TerraNode Programs 1–9 Evidence

## Test commands

Run from repository root:

```bash
python -m unittest -v terranode.tests.test_policy
python -m unittest -v terranode.tests.test_adapter
python -m unittest -v terranode.tests.test_program1
python -m unittest -v terranode.tests.test_program2_distributed
python -m unittest -v terranode.tests.test_program3_policy_independence
python -m unittest -v terranode.tests.test_program4_trust_weighted
python -m unittest -v terranode.tests.test_program5_multi_authority
python -m unittest -v terranode.tests.test_program6_semantic_interoperability
python -m unittest -v terranode.tests.test_program7_capability_security
python -m unittest -v terranode.tests.test_program8_public_submission_boundary
python -m unittest -v terranode.tests.test_program9_human_systems
```

## Expected outputs

- Policy test validates deterministic pro-rata split.
- Adapter test validates intention submission, conflict discovery, allocation writes, and closure.
- Program test validates full demo replay path and final totals.
- Program 2 test validates partition/reconnect convergence and conflict visibility.
- Program 3 test validates policy substitution with unchanged adapter flow.
- Program 4 test validates trust-weighted allocation in policy layer only.
- Program 5 test validates overlapping-authority mediated decisions.
- Program 6 test validates undefined semantics without mapping and defined semantics with mapping commitments.
- Program 7 test validates forged/non-transitive/expired capability defenses.
- Program 8 test validates boundary rate-limit and malformed-request controls.
- Program 9 test validates offline queue + reconnect preserving convergent history.
