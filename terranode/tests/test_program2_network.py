from __future__ import annotations

import unittest

from terranode.terranode.network import CoordinatorNode, InMemoryTransport, PartitionController
from terranode.terranode.policy import ProRataPolicy


class Program2NetworkTests(unittest.TestCase):
    def test_partition_duplicate_out_of_order_reconnect_converges(self) -> None:
        node_a = CoordinatorNode.create("node-a")
        node_b = CoordinatorNode.create("node-b")

        for node in (node_a, node_b):
            node.seed_subject(
                subject="warehouse-north",
                available=100.0,
                root_id="warehouse-north-root",
                capability_id="warehouse-north-capability",
            )

        transport = InMemoryTransport()
        transport.register(node_a)
        transport.register(node_b)
        partition = PartitionController(transport)
        partition.disconnect("node-a", "node-b")

        node_a.submit_claim("alice", "warehouse-north", 80.0, 100.0)
        node_b.submit_claim("bob", "warehouse-north", 60.0, 100.0)

        transport.enqueue_sync("node-a", "node-b")
        transport.enqueue_sync("node-b", "node-a")
        self.assertEqual(partition.flush(), [])

        partition.reconnect("node-a", "node-b")
        transport.enqueue_sync("node-a", "node-b", duplicate=True, out_of_order=True)
        transport.enqueue_sync("node-b", "node-a", duplicate=True, out_of_order=True)
        delivered = partition.flush()
        self.assertGreaterEqual(len(delivered), 2)

        self.assertEqual(len(node_a.find_conflicts("warehouse-north").claims), 2)
        self.assertEqual(len(node_b.find_conflicts("warehouse-north").claims), 2)

        node_a.apply_policy(ProRataPolicy(), "warehouse-north")
        transport.enqueue_sync("node-a", "node-b", duplicate=True, out_of_order=True)
        partition.flush()

        self.assertEqual(node_a.inventory_ids(), node_b.inventory_ids())
        self.assertEqual(node_a.adapter.replay().coordination.unresolved_intentions, [])
        self.assertEqual(node_b.adapter.replay().coordination.unresolved_intentions, [])


if __name__ == "__main__":
    unittest.main()
