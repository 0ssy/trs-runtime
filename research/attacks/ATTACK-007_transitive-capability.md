# ATTACK-007 — Transitive Capability Forgery

Goal: Forge delegation chain and consume it transitively.  
Hypothesis: Runtime may accept downstream authorization if chain references look plausible.

Expected: Reject forged root and dependent authorization.

Actual:
- Status: BLOCKED
- Evidence:
  - `d1_errors=['6.1 Authorization Traceability: missing authorization records: ghost-root']`
  - `d2_errors=['6.1 Authorization Traceability: missing authorization records: d1']`

Affected Rules:
- 6.1 Authorization Traceability

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_007_transitive_capability.py`)
