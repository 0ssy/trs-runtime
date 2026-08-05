# Interoperability Matrix

| Runtime | Language | Conformance | Syncs with Reference | Replay Compatible | Evidence |
| --- | --- | --- | --- | --- | --- |
| Reference | Python | ✅ | ✅ | ✅ | `research/interop/run_cycle_0012_baseline.py` |
| Independent #1 | Rust (reported) | pending | pending | pending | `research/cycles/CYCLE-0012_EXTERNAL_IMPLEMENTATION_REPORT_2026-08-04.md` |
| Independent #2 | Go | pending | pending | pending | pending |
| Independent #3 | Java | pending | pending | pending | pending |

## Execution sequence

1. Run conformance vectors in each implementation.
2. Submit base records in Runtime A.
3. Sync A -> Reference.
4. Replay on both sides and compare derived state invariants.
5. Repeat pairwise for every implementation pair.
