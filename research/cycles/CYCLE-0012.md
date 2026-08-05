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
- SDK interop harness: `research/interop/run_cycle_0012_sdk_cross_runtime.py`
- Latest summary: `evidence/interop/cycle0012_latest.json`
- Latest cross-impl summary: `evidence/interop/cycle0012_cross_latest.json`
- Latest SDK cross-runtime summary: `evidence/interop/cycle0012_sdk_cross_runtime_latest.json`
- Timestamped artifacts:
  - `evidence/interop/2026-08-03T134124Z_cycle0012_fixture.json`
  - `evidence/interop/2026-08-03T134124Z_cycle0012_summary.json`
  - `evidence/interop/2026-08-03T134124Z_cycle0012_cross_impl_summary.json`
  - `evidence/interop/2026-08-05T151416Z_cycle0012_rust_sdk_flow.json`
  - `evidence/interop/2026-08-05T151416Z_cycle0012_java_sdk_flow.json`
  - `evidence/interop/2026-08-05T151416Z_cycle0012_sdk_cross_runtime_summary.json`

### Current baseline result

- Source records: 8
- Imported records: 8
- Rejected records: none
- Inventory hash parity: pass
- Conflict visibility preserved: pass
- Replay unresolved intentions: none
- Rust SDK live interop to deployable node: pass
- Java SDK live interop to deployable node: pass
- External handoff package includes 9.5 track: `evidence/handoff/pre_pilot_external_handoff_latest.json`

## External report ingested (2026-08-04)

- Recorded in: `research/cycles/CYCLE-0012_EXTERNAL_IMPLEMENTATION_REPORT_2026-08-04.md`
- Reported status: functioning external implementation with no contradiction findings.
- Reported clarification candidates:
  - subject representation;
  - non-silent conflict wording;
  - authorization/delegation payload interoperability shape.
- TRS-0002 trigger status from report: not triggered.
- Closure note: strict Program 9.5 independence classification remains pending explicit attestation that only specification documents were used.

## Remaining closure requirement

External, non-reference-team implementation handoff and interoperability run must still be executed before closing CYCLE-0012 (SDK-level interop is now proven; independent runtime-level pairwise interop remains open).

## Pass criteria

- Interop succeeds for core flows without requiring TRS semantic change.
- Divergences are resolved at implementation/documentation level only.

## Fail conditions

- Reproducible semantic incompatibility requiring TRS core change.

## Amendment trigger

Open amendment candidate only with minimized reproducible contradiction + fixture + logs.
