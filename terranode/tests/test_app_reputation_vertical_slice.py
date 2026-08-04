from __future__ import annotations

import unittest

from terranode.terranode.reputation_application import run_reputation_vertical_slice


class AppReputationVerticalSliceTests(unittest.TestCase):
    def test_reputation_vertical_slice_emits_failure_replay_and_proof_artifacts(self) -> None:
        result = run_reputation_vertical_slice()
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.rejected_count, 2)
        self.assertEqual(set(result.allocations.keys()), {"alice", "bob"})
        self.assertAlmostEqual(sum(result.allocations.values()), 100.0, places=4)
        self.assertGreater(result.weights["alice"], result.weights["bob"])
        self.assertEqual(result.unresolved_intentions, [])
        self.assertEqual(result.orphan_grant_commitments, [])
        self.assertEqual(len(result.proofs), 2)
        for proof in result.proofs:
            self.assertTrue(proof.valid)
            self.assertEqual(proof.errors, [])
            self.assertGreaterEqual(len(proof.causal_path), 2)
            self.assertGreaterEqual(len(proof.authorization_path), 1)
        rejected_reasons = [receipt.reason for receipt in result.signal_receipts if not receipt.accepted]
        self.assertIn("missing claimant", rejected_reasons)
        self.assertIn("identity confidence out of range", rejected_reasons)
        self.assertIn("alice", result.replay_reputation)
        self.assertIn("bob", result.replay_reputation)


if __name__ == "__main__":
    unittest.main()
