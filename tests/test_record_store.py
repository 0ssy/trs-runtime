from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore


class RecordStoreTests(unittest.TestCase):
    def test_append_get_exists_children_all(self) -> None:
        store = RecordStore()
        root = Record(
            id="g1",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "temp", "value": 22},
            signature="sig:g1",
        )
        child = Record(
            id="c1",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "reduce", "horizon": "Q4"},
            causes=("g1",),
            signature="sig:c1",
        )
        store.append(root)
        store.append(child)

        self.assertTrue(store.exists("g1"))
        self.assertEqual(store.get("g1"), root)
        self.assertEqual([r.id for r in store.children("g1")], ["c1"])
        self.assertEqual([r.id for r in store.all()], ["g1", "c1"])

    def test_append_rejects_duplicate_id(self) -> None:
        store = RecordStore()
        record = Record(
            id="r1",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "temp", "value": 22},
            signature="sig:r1",
        )
        store.append(record)
        with self.assertRaises(ValueError):
            store.append(record)


if __name__ == "__main__":
    unittest.main()
