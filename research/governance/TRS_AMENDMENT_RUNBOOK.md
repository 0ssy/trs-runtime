# TRS Amendment Runbook

## 1) Open proposal

- Create amendment ID `TRS-000X`.
- Record target clauses and contradiction summary.
- Set status to `Proposed`.

## 2) Reproducibility review

- Attach fixture and exact commands.
- Evidence Reviewer runs commands independently.
- If reproducible, set state `Evidence Verified`; else `Deferred`.

## 3) Impact review

- Implementation Reviewer documents:
  - runtime surface impact,
  - conformance/test impact,
  - migration risk.
- Move to `Under Review`.

## 4) Ratification

- Steward Council records vote and rationale.
- If approved, set `Ratified`; otherwise `Rejected`.

## 5) Publication

- Update amendment log and status surfaces.
- Link all evidence artifacts.
- Announce effective version impact.
