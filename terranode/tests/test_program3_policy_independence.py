from __future__ import annotations

import unittest

from terranode.terranode.policy import (
    AllocationPolicy,
    AuctionPolicy,
    EmergencyOverridePolicy,
    PriorityPolicy,
    ProRataPolicy,
    WeightedPolicy,
)
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


class Program3PolicyIndependenceTests(unittest.TestCase):
    def test_multiple_policies_run_with_same_adapter_flow(self) -> None:
        policies: list[AllocationPolicy] = [
            ProRataPolicy(),
            PriorityPolicy({"alice": 2, "bob": 1}),
            WeightedPolicy({"alice": 1.2, "bob": 0.8}),
            AuctionPolicy({"alice": 80.0, "bob": 60.0}),
            EmergencyOverridePolicy("alice"),
        ]
        for index, policy in enumerate(policies, start=1):
            with self.subTest(policy=policy.__class__.__name__):
                adapter = TerraNodeRuntimeAdapter(node_id=f"policy-{index}")
                first = adapter.submit_intention("alice", "warehouse-7", 80.0, 100.0)
                second = adapter.submit_intention("bob", "warehouse-7", 60.0, 100.0)
                self.assertTrue(first.verification.valid)
                self.assertTrue(second.verification.valid)

                conflict_set = adapter.find_conflicts("warehouse-7")
                decision = policy.allocate(conflict_set)
                self.assertEqual(len(decision.allocations), 2)

                appended = adapter.apply_allocations(decision)
                self.assertEqual(len(appended), 4)
                replay = adapter.replay()
                self.assertEqual(replay.coordination.unresolved_intentions, [])


if __name__ == "__main__":
    unittest.main()
