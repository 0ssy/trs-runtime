from datetime import datetime, timezone
import unittest

from runtime.graph import Graph
from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore


class ConflictTests(unittest.TestCase):
    def test_conflicting_children_remain_visible(self) -> None:
        store = RecordStore()
        root = Record(
            id="root",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "state", "value": "open"},
            signature="sig:root",
        )
        c1 = Record(
            id="c1",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "close-A", "due_by": "2026-10-01"},
            causes=("root",),
            signature="sig:c1",
        )
        c2 = Record(
            id="c2",
            type=PrimitiveType.COMMITMENT,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "close-B", "due_by": "2026-10-01"},
            causes=("root",),
            signature="sig:c2",
        )
        store.append(root)
        store.append(c1)
        store.append(c2)

        graph = Graph(store)
        query = QueryEngine(store)
        self.assertEqual(set(graph.children("root")), {"c1", "c2"})
        self.assertEqual(set(r.id for r in query.query({"cause": "root"})), {"c1", "c2"})


if __name__ == "__main__":
    unittest.main()
