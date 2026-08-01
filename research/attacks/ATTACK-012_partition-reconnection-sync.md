# ATTACK-012 — Partition/Reconnection Sync

Goal: Break convergence by splitting nodes into partitions and reconnecting later.  
Hypothesis: Nodes may diverge permanently or reintroduce invalid records after reconnection.

Expected: Nodes converge after reconnection; invalid records remain rejected.

Actual:
- Status: BLOCKED
- Evidence:
  - `tests/test_multi_node_sim.py::test_partition_then_reconnect_converges_all_nodes`
  - `tests/test_multi_node_sim.py::test_invalid_record_is_rejected_across_network`

Affected Rules:
- 4.2 Causality
- 4.3 Local Sufficiency

Result: PASS (attack blocked)

Spec changed?: No  
Runtime changed?: Yes (added multi-node simulation subsystem)  
Tests added?: Yes (`tests/test_multi_node_sim.py`)
