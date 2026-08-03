# TRS Amendment Governance Charter (Draft)

## Purpose

Define a repeatable, auditable governance process for TRS amendments (TRS-000X) so outcomes are not person-dependent.

## Roles

- **Steward Council**: ratifies amendment outcomes.
- **Spec Editor**: prepares amendment text and traceability updates.
- **Evidence Reviewer**: verifies reproducibility of contradiction/evidence.
- **Implementation Reviewer**: confirms code/test impact and migration notes.

No single person may occupy all four roles for the same amendment.

## Amendment states

1. **Proposed**
2. **Under Review**
3. **Evidence Verified**
4. **Ratified**
5. **Rejected**
6. **Deferred**

## Required artifacts per amendment

- Problem statement linked to TRS clause(s)
- Minimal reproducible fixture + execution commands
- Evidence logs
- Implementation impact analysis
- Backward compatibility statement
- Ratification record with role signoff

## Ratification rule

An amendment reaches **Ratified** only if:

- Evidence Reviewer signs reproducibility,
- Implementation Reviewer signs impact analysis,
- Steward Council signs final decision.

## Auditability

All state transitions and signoffs must be written to an immutable decision log artifact.
