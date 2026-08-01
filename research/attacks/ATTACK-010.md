# ATTACK-010 — Hidden Conflict

Goal: Hide one branch of a conflicting sibling pair from query results.  
Hypothesis: Runtime may expose only one child in cause-based queries.

Expected: Both records visible.

Actual:
- Status: BLOCKED
- Evidence: `visible=['h1', 'h2']`

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_010_hidden_conflict.py`)
