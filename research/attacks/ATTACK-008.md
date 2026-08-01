# ATTACK-008 — Payload Sniffing

Goal: Trick runtime into inferring primitive from payload shape.  
Hypothesis: Observation envelope with commitment-like payload might be accepted as commitment semantics.

Expected: Reject against declared primitive validator.

Actual:
- Status: BLOCKED
- Evidence: `5.3 Payload Shape: missing payload keys: subject, value`

Result: PASS (attack blocked; payload-independence preserved)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_008_payload_sniffing.py`)
