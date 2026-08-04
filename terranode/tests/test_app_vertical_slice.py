from __future__ import annotations

import unittest

from terranode.terranode.application import app_validation_backlog, run_vertical_slice


class AppVerticalSliceTests(unittest.TestCase):
    def test_backlog_prioritizes_applications_and_defers_infra(self) -> None:
        backlog = app_validation_backlog()
        self.assertIn("terranode", backlog.flagship)
        self.assertIn("identity-service", backlog.domain_services)
        self.assertIn("openapi-generation-expansion", backlog.infrastructure_deferred)

    def test_vertical_slice_produces_workflow_failure_and_replay_evidence(self) -> None:
        result = run_vertical_slice()
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.rejected_count, 1)
        self.assertEqual(result.conflict_claim_count, 2)
        self.assertAlmostEqual(sum(result.allocations.values()), 100.0, places=4)
        self.assertEqual(result.unresolved_intentions, [])
        self.assertEqual(result.orphan_grant_commitments, [])
        self.assertEqual(len(result.proofs), 2)
        for proof in result.proofs:
            self.assertTrue(proof.valid)
            self.assertGreaterEqual(len(proof.causal_path), 2)
            self.assertGreaterEqual(len(proof.authorization_path), 1)
            self.assertEqual(proof.errors, [])
        self.assertTrue(any("rate limit" in receipt.reason for receipt in result.submission_receipts))


if __name__ == "__main__":
    unittest.main()
