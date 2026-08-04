from __future__ import annotations

import unittest

from terranode.terranode.workflow_application import run_workflow_vertical_slice


class AppWorkflowVerticalSliceTests(unittest.TestCase):
    def test_workflow_vertical_slice_emits_failure_replay_and_proof_artifacts(self) -> None:
        result = run_workflow_vertical_slice()
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.rejected_count, 1)
        self.assertAlmostEqual(sum(result.allocations.values()), 100.0, places=4)
        self.assertTrue(result.converged)
        self.assertEqual(result.unresolved_intentions, [])
        self.assertEqual(result.orphan_grant_commitments, [])
        self.assertEqual(len(result.proofs), 2)
        for proof in result.proofs:
            self.assertTrue(proof.valid)
            self.assertEqual(proof.errors, [])
            self.assertGreaterEqual(len(proof.causal_path), 2)
            self.assertGreaterEqual(len(proof.authorization_path), 1)


if __name__ == "__main__":
    unittest.main()
