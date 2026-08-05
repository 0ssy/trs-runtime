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
- `research/cycles/`: research cycle summaries and amendment decisions
- `logs/development/`: short daily engineering logs
- `evidence/`: persisted test-run and benchmark artifacts
- `experiments/`: disposable engineering validation scripts
- `STATUS.md`: live project status dashboard
- `schemas/`: schema artifacts (placeholder)
- `payloads/`: payload artifacts (placeholder)
- `docs/`: amendment log and external specification artifacts
- `trs-openapi/`: canonical network contract for node + SDK parity
- `trs-grpc/`: canonical gRPC contract for generated clients and services
- `trs-examples/`: small runnable reference apps for TRS usage patterns
- `trs-conformance/`: implementation-neutral conformance vectors and expected outcomes
- `trs-canonical/`: canonical serialization, hashing, and signing profiles
- `trs-network/`: normative HTTP wire protocol profile
- `trs-interop/`: cross-implementation interoperability matrix and reports
- `trs-formal/`: formal-method models (TLA+ starter)
- `trs-governance/`: amendment workflow, voting, accepted/rejected records
- `trs-independent-implementations/`: independent implementation evidence intake

## Canonical documentation files

- `docs/TRS_v1.0.pdf`
- `docs/Design_Record.pdf`
- `docs/Amendment_Log.md`
- `docs/SPEC_TRACEABILITY.md`
- `docs/RESEARCH_EXECUTION_MATRIX.md`

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s conformance -p "test_*.py"
python -m unittest -v tests.test_property_invariants
python -m unittest -v tests.test_fuzz_malformed_inputs
python -m unittest -v tests.test_mutation_checks
python -m unittest -v tests.test_multi_node_sim
```

## Run mutation checks

```bash
python experiments/0003-mutation/run_mutation_checks.py
```

## Run benchmarks

```bash
python benchmarks/run_benchmarks.py --records 2000 --out evidence/benchmarks/benchmark_baseline.json
```

## Compare benchmark runs

```bash
python benchmarks/compare_benchmarks.py --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json --current evidence/benchmarks/2026-08-01_phase15_baseline.json
```

## Run benchmark regression gate (writes history artifact)

```bash
python benchmarks/gate_benchmarks.py --mode quick --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json
python benchmarks/gate_benchmarks.py --mode pr --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json
python benchmarks/gate_benchmarks.py --mode nightly --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json
```

Policy split:

- `pr`: balanced gate for pull requests
- `nightly`: strict gate for stable machine/nightly run
- `nightly` includes small per-metric jitter overrides for volatile microbenchmarks

## Re-capture baseline on quiet machine (archives prior baseline)

```bash
python benchmarks/rebaseline_benchmarks.py --mode nightly --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json
```

## Run multi-node sync simulation

```bash
python experiments/0005-multi-node/run_multi_node_sim.py
```

## Run full validation cycle

```bash
python experiments/0006-validation/run_validation_cycle.py --gate-mode pr
```

## Run next research cycle (Programs 5-10)

```bash
python experiments/0013-cycle-0002/run_cycle_0002.py --scale-records 10000 100000
```

## Run in-memory performance RCA

```bash
python experiments/0014-inmemory-perf-rca/run_inmemory_perf_rca.py --records 200 2000 10000 --runs 3 --profile-records 10000
```

If you want to continue while still recording benchmark regressions:

```bash
python experiments/0006-validation/run_validation_cycle.py --gate-mode quick --allow-benchmark-regressions
```

## CI policy

- Pull requests run validation with `--gate-mode pr`.
- Pushes to `main` and nightly schedule run strict validation with `--gate-mode nightly`.
- Workflow file: `.github/workflows/validation.yml`.

## TerraNode integration boundary

Use `TerraNodeRuntimeAdapter` as TerraNode's only dependency on TRS-RR. TerraNode submits envelopes and consumes results; it does not implement or duplicate TRS verifier rules.
