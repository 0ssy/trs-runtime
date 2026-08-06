from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from terranode.terranode.program10_human_coordination import run_program10_study


class Program10HumanCoordinationTests(unittest.TestCase):
    def test_program10_study_generates_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "terranode-program10"
            result = run_program10_study(root)
            self.assertEqual(result.scenario_id, "alice-bob-offline-conflict")
            self.assertTrue(result.conflict_detected)
            self.assertEqual(result.task_creator, "alice")
            self.assertEqual(result.authorized_actor, "bob")
            self.assertEqual(result.completion_claimant, "bob")
            self.assertGreater(result.terranode_accuracy_mean, result.ordinary_accuracy_mean)

            required = [
                root / "scenarios" / "alice_bob_offline_conflict.json",
                root / "comparison" / "ordinary_logs" / "status_view.json",
                root / "comparison" / "ordinary_logs" / "activity_log.txt",
                root / "comparison" / "ordinary_logs" / "comments.md",
                root / "comparison" / "index.html",
                root / "comparison" / "terranode" / "timeline.json",
                root / "comparison" / "terranode" / "replay.json",
                root / "comparison" / "terranode" / "evidence.json",
                root / "comparison" / "terranode" / "authority.json",
                root / "comparison" / "terranode" / "conflict.json",
                root / "comparison" / "terranode" / "explanation.txt",
                root / "evaluation" / "questionnaire.md",
                root / "evaluation" / "metrics.csv",
                root / "evaluation" / "observations.md",
                root / "participants" / "participants.csv",
                root / "recordings" / "session_index.md",
                root / "report.md",
                root / "PROGRAM10.md",
            ]
            for path in required:
                self.assertTrue(path.exists(), msg=f"missing artifact: {path}")


if __name__ == "__main__":
    unittest.main()
