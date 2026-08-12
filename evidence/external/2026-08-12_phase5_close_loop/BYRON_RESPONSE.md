# byron follow-up (evidence update)

This captures what changed with direct evidence references.

## 1) App-layer boundary is now explicitly documented

- `docs/APP_LAYER_BOUNDARY.md`
- `docs/DEPLOYMENT_GUIDANCE.md`

Boundary statement used:

- TRS core = append-only verification/replay/query/explain.
- App layer = domain semantics, request-path behavior, edge policy and side effects.

## 2) Rule 4.5 partition interpretation is now explicit in behavior

- Amendment: `TRS-0004` (accepted) in `docs/Amendment_Log.md`.
- Runtime: `runtime/verifier.py::verify_non_silent_conflict`
- Coverage:
  - `conformance/conflict/test_conflict_visibility.py` (same-parent vs linear descendant semantics)
  - `tests/test_network_sync.py::test_partition_divergent_subject_chains_surface_conflict_on_reconnect`

## 3) Signed checkpoint anchoring landed

- Amendment: `TRS-0005` (accepted) in `docs/Amendment_Log.md`
- Runtime:
  - `runtime/sync.py::build_checkpoint_record`
  - `runtime/verifier.py::verify_checkpoint_anchor`
- Coverage:
  - `tests/test_checkpoints.py`

## 4) Fresh end-to-end validation evidence

- `evidence/test_runs/2026-08-12T081400Z_validation_cycle.log` (full cycle pass)
- `benchmarks/history/2026-08-12T081408Z_records-120_median-of-2.json`
