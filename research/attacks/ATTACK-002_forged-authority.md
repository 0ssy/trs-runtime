# ATTACK-002 — Forged Authority

Goal: Submit a forged commitment with valid shape/schema/signature but invalid authorization reference.  
Hypothesis: Authorization traversal might be bypassed.

Expected: Reject via Rule 6.1.

Actual:
- Status: BLOCKED
- Evidence: `6.1 Authorization Traceability: missing authorization records: ghost-capability`

Affected Rules:
- 6.1 Authorization Traceability

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_002_forged_authority.py`)
