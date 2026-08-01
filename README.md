# TRS Runtime

TRS runtime implementation with strict payload-independence:

- The record envelope declares the primitive type.
- The verifier validates payload structure against the declared primitive.
- The runtime never infers primitive type from payload.

## Layout

- `runtime/`: core runtime modules
- `runtime/terranode_adapter.py`: TerraNode integration boundary API
- `runtime/storage.py`: `StorageEngine`, `RecordStore` (in-memory), `SQLiteStorage`, `LMDBStorage`, `RocksDBStorage`
- `runtime/crypto.py`: Ed25519 key generation, signing, verification, rotation, delegation graph
- `runtime/network_sync.py`: inventory exchange and unordered verified record transfer
- `runtime/replay.py`: deterministic replay engine for derived views
- `runtime/benchmark.py`: Phase 15 benchmark harness
- `libraries/`: derived read-only libraries (identity, reputation, contracts, workflow, capabilities, trust, policy)
- `conformance/`: specification-facing conformance tests
- `tests/`: focused unit tests
- `attacks/`: executable adversarial attack scripts
- `research/attacks/`: persisted attack records
- `logs/development/`: short daily engineering logs
- `evidence/`: persisted test-run and benchmark artifacts
- `STATUS.md`: live project status dashboard
- `schemas/`: schema artifacts (placeholder)
- `payloads/`: payload artifacts (placeholder)
- `docs/`: amendment log and external specification artifacts

## Canonical documentation files

- `docs/TRS_v1.0.pdf`
- `docs/Design_Record.pdf`
- `docs/Amendment_Log.md`
- `docs/SPEC_TRACEABILITY.md`

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s conformance -p "test_*.py"
```

## Run benchmarks

```bash
python benchmarks/run_benchmarks.py --records 2000 --out evidence/benchmarks/benchmark_baseline.json
```

## Compare benchmark runs

```bash
python benchmarks/compare_benchmarks.py --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json --current evidence/benchmarks/2026-08-01_phase15_baseline.json
```

## TerraNode integration boundary

Use `TerraNodeRuntimeAdapter` as TerraNode's only dependency on TRS-RR. TerraNode submits envelopes and consumes results; it does not implement or duplicate TRS verifier rules.
