# CYCLE-0013 — TerraNode Program 9.6 Mechanized Verification

## Status

In progress (expanded mechanized model-check and TLC run both passing on bounded model; broader proof-depth expansion still open).

## Depends on

- CYCLE-0012 complete.

## New question

Do machine-checked models uphold TRS axioms and conflict/closure guarantees under concurrency?

## Entry criteria

- Property inventory extracted from accepted TRS clauses.
- Modeling language/toolchain selected (TLA+ and/or Coq).

## Evidence targets

- Formal model source and run commands.
- Model-check/proof output artifacts.
- Counterexample traces (if any) with mapping back to TRS clauses.

## Baseline initialized

- Harness: `research/formal/run_cycle_0013_model_check.py`
- TLC harness: `research/formal/run_cycle_0013_tlc.py`
- Latest summary: `evidence/formal/cycle0013_latest.json`
- Latest TLC summary: `evidence/formal/cycle0013_tlc_latest.json`
- Timestamped artifacts:
  - `evidence/formal/2026-08-03T134219Z_cycle0013_model_check.json`
  - `evidence/formal/2026-08-05T144432Z_cycle0013_model_check.json`
  - `evidence/formal/2026-08-05T145123Z_cycle0013_tlc.json`
  - `evidence/formal/tlc/2026-08-05T145123Z_cycle0013_tlc.log`

### Current baseline result

- States explored: 441
- Terminal states: 1
- Max depth: 16
- Invariants checked:
  - append-only growth per node
  - causal and authorization closure per node
  - conflict visibility when dual intentions coexist
  - replay equivalence for equal inventories
  - terminal convergence under synchronization
  - terminal closure (no unresolved intentions)
- Violations: none

### TLC result (bounded TLA+ run)

- Status: pass
- States generated: 2083
- Distinct states: 441
- Search depth: 17
- Duration: 3s

## Pass criteria

- Model-check/proof runs complete and satisfy targeted properties.
- No unresolved counterexample violating accepted semantics.

## Fail conditions

- Valid counterexample contradicts current TRS semantics.

## Amendment trigger

Open amendment candidate when counterexample is reproducible and spec-linked.
