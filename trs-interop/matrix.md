# Interoperability Matrix

| Runtime | Language | Conformance | Syncs with Reference | Replay Compatible | Evidence |
| --- | --- | --- | --- | --- | --- |
| Reference | Python | ✅ | ✅ | ✅ | `evidence/interop/2026-08-06T120623Z_cycle0012_summary.json`, `evidence/interop/2026-08-06T120623Z_cycle0012_cross_impl_summary.json` |
| SDK client | Rust | n/a (client) | ✅ | ✅ | `evidence/interop/2026-08-06T120624Z_cycle0012_rust_sdk_flow.json`, `evidence/interop/2026-08-06T120624Z_cycle0012_sdk_cross_runtime_summary.json` |
| SDK client | Java | n/a (client) | ✅ | ✅ | `evidence/interop/2026-08-06T120624Z_cycle0012_java_sdk_flow.json`, `evidence/interop/2026-08-06T120624Z_cycle0012_sdk_cross_runtime_summary.json` |
| Independent #1 | Rust (reported) | pending | pending | pending | `research/cycles/CYCLE-0012_EXTERNAL_IMPLEMENTATION_REPORT_2026-08-04.md` |
| Independent #2 | Go | pending | pending | pending | pending |
| Independent #3 | Java | pending | pending | pending | pending |

## Execution sequence

1. Run conformance vectors in each implementation.
2. Submit base records in Runtime A.
3. Sync A -> Reference.
4. Replay on both sides and compare derived state invariants.
5. Repeat pairwise for every implementation pair.

## Latest run snapshot

- Timestamp: `2026-08-06T120623Z`
- Source records imported: `8/8`
- Rejected: `[]`
- Inventory hash match: `true`
- Conflict visible: `true`
- Replay unresolved intentions: `[]`
- SDK cross-runtime summary (`2026-08-06T120624Z`): Rust SDK + Java SDK to deployable node pass (`cross_runtime_pass=true`).
- Gate 2 closure (current cycle): pass.
