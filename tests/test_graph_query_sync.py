from datetime import datetime, timezone
import unittest

from runtime.graph import Graph
from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.sync import sync_append_only
from runtime.verifier import Verifier


class GraphQuerySyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = RecordStore()
        self.verifier = Verifier(self.store)
        self.g = Record(
            id="g",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "s", "value": 1},
            authorization=("g",),
            signature="sig:g",
        )
        self.a = Record(
            id="a",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "grow", "horizon": "Q2"},
            causes=("g",),
            signature="sig:a",
        )
        self.b = Record(
            id="b",
            type=PrimitiveType.COMMITMENT,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "deliver", "due_by": "2026-12-31"},
            causes=("a",),
            authorization=("g",),
            signature="sig:b",
        )
        for record in (self.g, self.a, self.b):
            self.store.append(record)

    def test_graph_operations(self) -> None:
        graph = Graph(self.store)
        self.assertEqual(graph.parents("b"), ["a"])
        self.assertEqual(set(graph.ancestors("b")), {"a", "g"})
        self.assertEqual(set(graph.descendants("g")), {"a", "b"})
        self.assertEqual(graph.common_ancestor("a", "b"), "a")
        order = graph.topological_order()
        self.assertLess(order.index("g"), order.index("a"))
        self.assertLess(order.index("a"), order.index("b"))

    def test_query_is_read_only(self) -> None:
        query = QueryEngine(self.store)
        before = len(self.store.all())
        matches = query.query({"type": PrimitiveType.INTENTION})
        after = len(self.store.all())
        self.assertEqual(before, after)
        self.assertEqual([r.id for r in matches], ["a"])

    def test_sync_appends_only_verified_records(self) -> None:
        local = RecordStore()
        local.append(self.g)
        verifier = Verifier(local)
        bad = Record(
            id="bad",
            type=PrimitiveType.OBSERVATION,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"action": "forge", "due_by": "2026-12-31"},
            signature="sig:bad",
        )
        result = sync_append_only(local, [self.a, self.b, bad], verifier)
        self.assertEqual(result.appended_ids, ["a", "b"])
        self.assertFalse(local.exists("bad"))


if __name__ == "__main__":
    unittest.main()
