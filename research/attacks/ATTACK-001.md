# ATTACK-001 — Duplicate IDs

Goal: Insert a second record with an existing ID.  
Hypothesis: Runtime might allow duplicate IDs in append flow.

Expected: Reject.

Actual:
- Status: BLOCKED
- Evidence: `4.1 Immutability: record id already exists: dup`

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_001_duplicate_ids.py`)
