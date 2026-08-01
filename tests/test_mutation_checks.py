from __future__ import annotations

import unittest

from runtime.mutation_checks import run_mutation_checks


class MutationChecksTests(unittest.TestCase):
    def test_mutation_checks_kill_all_current_mutants(self) -> None:
        summary = run_mutation_checks()
        self.assertEqual(summary.total, 5)
        self.assertEqual(summary.killed, 5, f"survivors: {[r.mutant for r in summary.results if not r.killed]}")
        self.assertEqual(summary.survived, 0)


if __name__ == "__main__":
    unittest.main()
