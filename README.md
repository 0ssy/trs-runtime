# TRS Runtime

TRS runtime implementation with strict payload-independence:

- The record envelope declares the primitive type.
- The verifier validates payload structure against the declared primitive.
- The runtime never infers primitive type from payload.

## Layout

- `runtime/`: core runtime modules
- `runtime/terranode_adapter.py`: TerraNode integration boundary API
- `libraries/`: derived read-only libraries (identity, reputation, contracts, workflow, capabilities, trust, policy)
- `conformance/`: specification-facing conformance tests
- `tests/`: focused unit tests
- `attacks/`: executable adversarial attack scripts
- `research/attacks/`: persisted attack records
- `logs/development/`: short daily engineering logs
- `schemas/`: schema artifacts (placeholder)
- `payloads/`: payload artifacts (placeholder)
- `docs/`: amendment log and external specification artifacts

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s conformance -p "test_*.py"
```

## TerraNode integration boundary

Use `TerraNodeRuntimeAdapter` as TerraNode's only dependency on TRS-RR. TerraNode submits envelopes and consumes results; it does not implement or duplicate TRS verifier rules.
