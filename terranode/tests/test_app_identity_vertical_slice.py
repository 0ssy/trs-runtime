from __future__ import annotations

import unittest

from terranode.terranode.identity_application import run_identity_vertical_slice


class AppIdentityVerticalSliceTests(unittest.TestCase):
    def test_identity_vertical_slice_emits_workflow_failure_and_replay_evidence(self) -> None:
        result = run_identity_vertical_slice()
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.rejected_count, 2)
        self.assertEqual(
            result.directory,
            {
                "did:trs:alice": "alice",
                "did:trs:bob": "bob",
            },
        )
        self.assertIn("alice", result.replay_identities)
        self.assertIn("bob", result.replay_identities)
        self.assertIn("identity-registrar", result.replay_identities)
        self.assertEqual(len(result.proofs), 2)
        for proof in result.proofs:
            self.assertTrue(proof.valid)
            self.assertEqual(proof.errors, [])
            self.assertGreaterEqual(len(proof.causal_path), 2)
            self.assertGreaterEqual(len(proof.authorization_path), 1)
        reasons = [receipt.reason for receipt in result.submission_receipts if not receipt.accepted]
        self.assertIn("duplicate identity", reasons)
        self.assertIn("missing identity", reasons)


if __name__ == "__main__":
    unittest.main()
