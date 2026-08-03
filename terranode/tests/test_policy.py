from __future__ import annotations

import unittest

from terranode.terranode.policy import Claim, ConflictSet, ProRataPolicy


class PolicyTests(unittest.TestCase):
    def test_pro_rata_policy_allocates_expected_ratio(self) -> None:
        policy = ProRataPolicy()
        conflict_set = ConflictSet(
            subject="warehouse-7",
            available=100.0,
            claims=[
                Claim(claim_id="a", claimant="alice", amount=80.0),
                Claim(claim_id="b", claimant="bob", amount=60.0),
            ],
        )
        decision = policy.allocate(conflict_set)
        by_claimant = {allocation.claimant: allocation.granted for allocation in decision.allocations}
        self.assertAlmostEqual(by_claimant["alice"], 57.142857, places=4)
        self.assertAlmostEqual(by_claimant["bob"], 42.857143, places=4)


if __name__ == "__main__":
    unittest.main()
