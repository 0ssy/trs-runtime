from __future__ import annotations

from datetime import datetime, timezone
import unittest

from runtime.multi_node_sim import (
    fully_connected_links,
    make_linear_records,
    make_node,
    simulate_partitioned_sync,
)
from runtime.record import PrimitiveType, Record


class MultiNodeSimulationTests(unittest.TestCase):
    def test_partition_then_reconnect_converges_all_nodes(self) -> None:
        chain = make_linear_records(8)
        n0 = make_node("n0", chain)
        n1 = make_node("n1", chain[:4])
        n2 = make_node("n2", chain[:2])
        n3 = make_node("n3", [])

        rounds = [
            [("n0", "n1"), ("n2", "n3")],  # partitioned islands
            [("n0", "n1"), ("n2", "n3")],
            [("n1", "n2")],  # reconnect bridge
            fully_connected_links(["n0", "n1", "n2", "n3"]),
            fully_connected_links(["n0", "n1", "n2", "n3"]),
        ]
        result = simulate_partitioned_sync([n0, n1, n2, n3], rounds)
        self.assertTrue(result.converged)
        expected_ids = sorted(record.id for record in chain)
        for node_name, inventory in result.inventories.items():
            self.assertEqual(inventory, expected_ids, node_name)

    def test_invalid_record_is_rejected_across_network(self) -> None:
        chain = make_linear_records(5)
        invalid = Record(
            id="bad",
            type=PrimitiveType.COMMITMENT,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "forge", "due_by": "2027-01-01"},
            authorization=("ghost",),
            signature="sig:bad",
        )
        source = make_node("source", [*chain, invalid])
        peer_a = make_node("peer-a", [])
        peer_b = make_node("peer-b", [])

        rounds = [
            [("source", "peer-a"), ("source", "peer-b")],
            [("peer-a", "peer-b")],
        ]
        result = simulate_partitioned_sync([source, peer_a, peer_b], rounds)
        self.assertNotIn("bad", result.inventories["peer-a"])
        self.assertNotIn("bad", result.inventories["peer-b"])
        rejected = [rid for round_item in result.rounds for ids in round_item.rejected_by_target.values() for rid in ids]
        self.assertIn("bad", rejected)


if __name__ == "__main__":
    unittest.main()
