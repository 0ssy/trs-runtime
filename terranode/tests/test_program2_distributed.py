from __future__ import annotations

import unittest

from terranode.terranode.policy import ProRataPolicy
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


class Program2DistributedTests(unittest.TestCase):
    def test_partition_reconnect_converges_without_runtime_changes(self) -> None:
        node_a = TerraNodeRuntimeAdapter(node_id="node-a")
        node_b = TerraNodeRuntimeAdapter(node_id="node-b")

        node_a.seed_subject(
            subject="warehouse-north",
            available=100.0,
            root_id="warehouse-north-root",
            capability_id="warehouse-north-capability",
        )
        node_b.seed_subject(
            subject="warehouse-north",
            available=100.0,
            root_id="warehouse-north-root",
            capability_id="warehouse-north-capability",
        )

        a_submit = node_a.submit_intention("alice", "warehouse-north", 80.0, 100.0)
        b_submit = node_b.submit_intention("bob", "warehouse-north", 60.0, 100.0)
        self.assertTrue(a_submit.verification.valid)
        self.assertTrue(b_submit.verification.valid)

        self.assertEqual(len(node_a.find_conflicts("warehouse-north").claims), 1)
        self.assertEqual(len(node_b.find_conflicts("warehouse-north").claims), 1)

        peer_to_a, a_to_peer = node_a.sync_with_peer(node_b)
        self.assertEqual(peer_to_a.rejected_ids, [])
        self.assertEqual(a_to_peer.rejected_ids, [])

        a_conflicts = node_a.find_conflicts("warehouse-north")
        b_conflicts = node_b.find_conflicts("warehouse-north")
        self.assertEqual(len(a_conflicts.claims), 2)
        self.assertEqual(len(b_conflicts.claims), 2)

        a_decision = ProRataPolicy().allocate(a_conflicts)
        b_decision = ProRataPolicy().allocate(b_conflicts)
        node_a.apply_allocations(a_decision)
        node_b.apply_allocations(b_decision)

        second_peer_to_a, second_a_to_peer = node_a.sync_with_peer(node_b)
        self.assertEqual(second_peer_to_a.rejected_ids, [])
        self.assertEqual(second_a_to_peer.rejected_ids, [])

        self.assertEqual(
            sorted(record.id for record in node_a.store.all()),
            sorted(record.id for record in node_b.store.all()),
        )
        self.assertEqual(node_a.replay().coordination.unresolved_intentions, [])
        self.assertEqual(node_b.replay().coordination.unresolved_intentions, [])


if __name__ == "__main__":
    unittest.main()
