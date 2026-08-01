# ATTACK-005 — Conflicting Commitments Visibility

Goal: Hide conflict by appending divergent siblings from the same cause.  
Hypothesis: Runtime may suppress one branch or overwrite visibility.

Expected: Both branches remain visible.

Actual:
- Status: BLOCKED
- Evidence: `children=['c1', 'c2']`

Affected Rules:
- 4.5 Non-Silent Conflict

Result: PASS (attack blocked; non-silent conflict visibility preserved)

Spec changed?: No  
Runtime changed?: No  
Tests added?: Yes (`attacks/attack_005_conflicting_commitments.py`)
