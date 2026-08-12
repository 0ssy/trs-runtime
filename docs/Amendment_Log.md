# Amendment Log

## TRS-0001 — Accepted

- Status: Accepted
- Scope: Payload-independence enforcement in runtime envelope handling.

## TRS-0002 — Accepted

- Status: Accepted
- Issue: Conflict visibility over-classified same-parent fan-out as conflict by relying only on payload inequality.
- Justification: Independent agents can legitimately create different intentions under a shared parent while acting on different resources.
- Counterexample: Two intentions with the same parent but different subjects (for example, `warehouse-7/slot-a` vs `warehouse-7/slot-b`) were treated as conflict despite not being mutually exclusive.
- Resolution: Introduce `Record.subject` with backward-compatible defaulting and scope non-silent conflict to siblings where `sibling.subject == record.subject` and payloads differ.

## TRS-0003 — Accepted

- Status: Accepted
- Issue: Caller-supplied or random record IDs can produce silent history divergence for equivalent logical records across implementations.
- Resolution: Record IDs are now content-derived from canonical envelope identity bytes (canonical form excluding `id` and `signature`) with domain-separated hash prefix.
- Runtime surface:
  - `runtime/canonical.py::derive_record_id`
  - `runtime/record.py::Record.create`

## TRS-0004 — Accepted

- Status: Accepted
- Issue: Rule 4.5 wording constrained conflict detection to immediate sibling fan-out and could miss partition-branch divergence on reconnect.
- Resolution: Rule 4.5 now treats conflict visibility as:
  - immediate same-parent, same-subject, payload-different conflicts, and
  - divergent same-subject branches sharing a causal predecessor (ancestor scope), while excluding direct ancestor-descendant linear updates.
- Runtime surface:
  - `runtime/verifier.py::verify_non_silent_conflict`
  - `conformance/conflict/test_conflict_visibility.py`
  - `tests/test_network_sync.py::test_partition_divergent_subject_chains_surface_conflict_on_reconnect`

## TRS-0005 — Accepted

- Status: Accepted
- Issue: Without signed checkpoint anchors, a compromised key can attempt plausible backdated inserts.
- Resolution: Add checkpoint anchoring rule and checkpoint record support:
  - checkpoint observation payload (`subject=trs.checkpoint`) with inventory hash and heads,
  - non-checkpoint records must be newer than the latest checkpoint anchor timestamp.
- Runtime surface:
  - `runtime/sync.py::build_checkpoint_record`
  - `runtime/verifier.py::verify_checkpoint_anchor`
  - `tests/test_checkpoints.py`

## Documentation Addenda (Non-Normative)

- `docs/DESIGN_RECORD_LINEAGE_ADDENDUM.md` adds lineage references (Winograd & Flores, 1986; Suchman, 1994) without changing TRS v1.0 normative content.
