# TerraNode Program 1

TerraNode Program 1 is a consumer-validation experiment over TRS runtime.

## Layout

- `terranode/policy.py`: pure allocation policy types and logic.
- `terranode/runtime_adapter.py`: TRS integration boundary.
- `terranode/main.py`: scarcity demonstration flow.
- `tests/`: policy, adapter, and end-to-end tests.
- `docs/ROADMAP_P2_P9.md`: dependency-ordered post-v1.0 research stack.
- `examples/scarcity_demo.py`: runnable demo entrypoint.

## Run tests

```bash
python -m unittest -v terranode.tests.test_policy
python -m unittest -v terranode.tests.test_adapter
python -m unittest -v terranode.tests.test_program1
python -m unittest -v terranode.tests.test_program2_distributed
python -m unittest -v terranode.tests.test_program3_policy_independence
```

## Run demo

```bash
python terranode/examples/scarcity_demo.py
```
