from datetime import datetime, timezone
import unittest

from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore


class IdentityTests(unittest.TestCase):
    def test_local_query_only_reads_local_records(self) -> None:
        store = RecordStore()
        record = Record(
            id="id-1",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "identity", "value": "alice"},
            signature="sig:id-1",
        )
        store.append(record)
        engine = QueryEngine(store)
        before = len(store.all())
        found = engine.query({"author": "alice"})
        after = len(store.all())
        self.assertEqual(before, after)
        self.assertEqual([r.id for r in found], ["id-1"])


if __name__ == "__main__":
    unittest.main()
