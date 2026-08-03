from __future__ import annotations

import unittest

from terranode.terranode.policy import ProRataPolicy
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


class AdapterTests(unittest.TestCase):
    def test_adapter_submits_conflicts_allocates_and_closes(self) -> None:
        adapter = TerraNodeRuntimeAdapter()
        policy = ProRataPolicy()

        r1 = adapter.submit_intention("alice", "warehouse-7", 80.0, 100.0)
        r2 = adapter.submit_intention("bob", "warehouse-7", 60.0, 100.0)
        self.assertTrue(r1.verification.valid)
        self.assertTrue(r2.verification.valid)

        conflict_set = adapter.find_conflicts("warehouse-7")
        self.assertEqual(len(conflict_set.claims), 2)

        decision = policy.allocate(conflict_set)
        appended = adapter.apply_allocations(decision)
        self.assertEqual(len(appended), 4)

        after = adapter.find_conflicts("warehouse-7")
        self.assertEqual(len(after.claims), 0)


if __name__ == "__main__":
    unittest.main()
