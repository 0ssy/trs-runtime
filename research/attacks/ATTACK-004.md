# ATTACK-004 — Schema Mismatch

Goal: Submit a commitment declared with an observation schema.  
Hypothesis: Runtime may ignore declared primitive/schema consistency.

Expected: Reject via Rule 5.1.

Actual:
- Status: BLOCKED
- Evidence: `5.1 Schema Declaration: schema trs.observation.v1 does not match declared primitive Commitment`

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_004_schema_mismatch.py`)
