from __future__ import annotations

import unittest

from terranode.terranode.authority import MultiAuthorityCoordinator
from terranode.terranode.policy import PriorityPolicy, ProRataPolicy
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


class Program5MultiAuthorityTests(unittest.TestCase):
    def test_overlapping_authorities_mediate_without_runtime_changes(self) -> None:
        adapter = TerraNodeRuntimeAdapter(node_id="p5")
        adapter.submit_intention("alice", "water-1", 80.0, 100.0)
        adapter.submit_intention("bob", "water-1", 60.0, 100.0)
        conflict_set = adapter.find_conflicts("water-1")
        self.assertEqual(len(conflict_set.claims), 2)

        coordinator = MultiAuthorityCoordinator(influences={"council": 1.0, "cooperative": 2.0})
        mediated = coordinator.decide(
            conflict_set=conflict_set,
            authority_policies={
                "council": ProRataPolicy(),
                "cooperative": PriorityPolicy({"alice": 1, "bob": 2}),
            },
        )
        self.assertEqual(mediated.authority, "mediated")
        self.assertEqual(len(mediated.decision.allocations), 2)

        adapter.apply_allocations(mediated.decision)
        self.assertEqual(adapter.replay().coordination.unresolved_intentions, [])


if __name__ == "__main__":
    unittest.main()
