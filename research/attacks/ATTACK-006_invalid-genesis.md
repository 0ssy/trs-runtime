# ATTACK-006 — Invalid Genesis

Goal: Append genesis-like record without signature.  
Hypothesis: Genesis might bypass signature requirements.

Expected: Reject via Rule 5.2.

Actual:
- Status: BLOCKED
- Evidence: `5.2 Signature Presence: missing signature`

Affected Rules:
- 5.2 Signature Presence

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_006_invalid_genesis.py`)
