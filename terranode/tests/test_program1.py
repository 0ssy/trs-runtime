from __future__ import annotations

import unittest

from terranode.terranode.main import run_demo


class Program1Tests(unittest.TestCase):
    def test_program1_scarcity_demo(self) -> None:
        allocations = run_demo()
        self.assertAlmostEqual(allocations["alice"], 57.142857, places=4)
        self.assertAlmostEqual(allocations["bob"], 42.857143, places=4)
        self.assertAlmostEqual(sum(allocations.values()), 100.0, places=4)


if __name__ == "__main__":
    unittest.main()
