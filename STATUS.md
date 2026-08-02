# TRS Runtime Status

## Specification

- TRS v1.0 Draft: Frozen

## Amendments

- TRS-0001: Accepted
- TRS-0002: None
- Research Method Matrix: `docs/RESEARCH_EXECUTION_MATRIX.md` active
- Current cycle record: `research/cycles/CYCLE-0001.md` (TRS-0002 not triggered)
- Current cycle record: `research/cycles/CYCLE-0002.md` (closed; external Program 10 submission complete)
- Current cycle record: `research/cycles/CYCLE-0003.md` (Program 11 closed; TRS refined; TRS-0002 not triggered)

## Runtime

- Verifier: Complete
- Explain: Complete
- Storage Abstraction: Complete
- Persistence: Complete (SQLite + LMDB + RocksDB)
- Crypto (Ed25519): Complete
- Network Sync Layer: Complete (inventory exchange + unordered ingest)
- Replay Engine: Complete
- Benchmark Harness: Complete
- Graph: Complete
- Query: Complete
- Sync: Complete
- Adapter: Complete

## Verification

- Unit Tests: 44 / 44 Passing
- Conformance: 7 / 7 Passing
- Attack Suite Runner: 10 / 10 Blocked
- Attack Records: 12 total (ATTACK-001 .. ATTACK-012)
- Property Tests: 4 invariant properties (Hypothesis) passing
- Fuzzing: 2 generated fuzz properties passing
- Mutation Checks: 5 / 5 mutants killed
- Benchmarks: baseline + history + median regression gate configured (PR/nightly policy)

## Evidence

- `evidence/benchmarks/2026-08-01_phase15_baseline.json` (re-captured on current code)
- `evidence/benchmarks/archive/2026-08-01_phase15_baseline_2026-08-02T165225Z.json`
- `benchmarks/history/*.json` (rolling benchmark history artifacts)
- `evidence/traces/2026-08-01_multi_node_sim.json` (regenerated on current code)
- `evidence/test_runs/2026-08-02T162349Z_validation_cycle.log` (nightly + allow-benchmark-regressions: pass)
- `evidence/test_runs/2026-08-02T165226Z_validation_cycle.log` (nightly + allow-benchmark-regressions: pass)

## Reference Runtime

- Version: v0.1.0-reference-runtime (checkpoint locked; tag ready)
