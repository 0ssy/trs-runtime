# TRS Runtime

TRS runtime implementation with strict payload-independence:

- The record envelope declares the primitive type.
- The verifier validates payload structure against the declared primitive.
- The runtime never infers primitive type from payload.

## Layout

- `runtime/`: core runtime modules
- `libraries/`: derived read-only libraries (identity, reputation, contracts, workflow, capabilities, trust, policy)
- `conformance/`: specification-facing conformance tests
- `tests/`: focused unit tests
- `schemas/`: schema artifacts (placeholder)
- `payloads/`: payload artifacts (placeholder)
- `docs/`: amendment log and external specification artifacts

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s conformance -p "test_*.py"
```
