from __future__ import annotations

import unittest

from terranode.terranode.policy import ProRataPolicy
from terranode.terranode.sdk import TerraNodePythonClient


class Program910SdkTests(unittest.TestCase):
    def test_python_sdk_claim_submission_and_resolution(self) -> None:
        client = TerraNodePythonClient()
        alice = client.submit_claim(claimant="alice", subject="warehouse-7", amount=80.0, available=100.0)
        bob = client.submit_claim(claimant="bob", subject="warehouse-7", amount=60.0, available=100.0)
        self.assertTrue(alice.accepted)
        self.assertTrue(bob.accepted)

        decision = client.resolve_subject("warehouse-7", ProRataPolicy())
        self.assertEqual(len(decision.allocations), 2)
        total = sum(allocation.granted for allocation in decision.allocations)
        self.assertAlmostEqual(total, 100.0, places=4)


if __name__ == "__main__":
    unittest.main()
