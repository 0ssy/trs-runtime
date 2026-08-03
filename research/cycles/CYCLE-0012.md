# CYCLE-0012 — TerraNode Program 9.5 Independent Second Implementation

## Status

In progress (reference + independent baseline interop complete).

## Depends on

- CYCLE-0011 complete.

## New question

Can a second, independent implementation built from frozen TRS documents interoperate with the reference implementation?

## Entry criteria

- Frozen TRS docs and amendment log are published as canonical input.
- Second implementation team has no dependency on reference code internals.

## Evidence targets

- Independent implementation repository and build instructions.
- Cross-implementation conformance run logs.
- Interop trace for record exchange, verification, replay, and conflict visibility.

## Baseline initialized

- Harness: `research/interop/run_cycle_0012_baseline.py`
- Independent harness: `research/interop/run_cycle_0012_cross_impl.py`
- Latest summary: `evidence/interop/cycle0012_latest.json`
- Latest cross-impl summary: `evidence/interop/cycle0012_cross_latest.json`
- Timestamped artifacts:
  - `evidence/interop/2026-08-03T134124Z_cycle0012_fixture.json`
  - `evidence/interop/2026-08-03T134124Z_cycle0012_summary.json`
  - `evidence/interop/2026-08-03T134124Z_cycle0012_cross_impl_summary.json`

### Current baseline result

- Source records: 8
- Imported records: 8
- Rejected records: none
- Inventory hash parity: pass
- Conflict visibility preserved: pass
- Replay unresolved intentions: none

## Remaining closure requirement

External, non-reference-team implementation handoff and interoperability run must still be executed before closing CYCLE-0012.

## Pass criteria

- Interop succeeds for core flows without requiring TRS semantic change.
- Divergences are resolved at implementation/documentation level only.

## Fail conditions

- Reproducible semantic incompatibility requiring TRS core change.

## Amendment trigger

Open amendment candidate only with minimized reproducible contradiction + fixture + logs.
