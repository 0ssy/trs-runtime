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
