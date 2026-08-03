from __future__ import annotations

import unittest

from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter
from terranode.terranode.trust import TrustModel, TrustSignal, TrustWeightedPolicy


class Program4TrustWeightedTests(unittest.TestCase):
    def test_trust_weighted_policy_stays_policy_layer(self) -> None:
        adapter = TerraNodeRuntimeAdapter(node_id="p4")
        first = adapter.submit_intention("alice", "warehouse-7", 80.0, 100.0)
        second = adapter.submit_intention("bob", "warehouse-7", 60.0, 100.0)
        self.assertTrue(first.verification.valid)
        self.assertTrue(second.verification.valid)

        signals = [
            TrustSignal(claimant="alice", identity_confidence=0.95, reputation_score=0.9, age_days=2.0),
            TrustSignal(claimant="bob", identity_confidence=0.7, reputation_score=0.6, age_days=20.0),
        ]
        decision = TrustWeightedPolicy(TrustModel(half_life_days=30.0), signals).allocate(
            adapter.find_conflicts("warehouse-7")
        )
        by_claimant = {allocation.claimant: allocation.granted for allocation in decision.allocations}
        self.assertGreater(by_claimant["alice"], by_claimant["bob"])
        adapter.apply_allocations(decision)
        self.assertEqual(adapter.replay().coordination.unresolved_intentions, [])


if __name__ == "__main__":
    unittest.main()
