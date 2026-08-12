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

    def test_record_payload_is_frozen_and_isolated_from_input_mutation(self) -> None:
        payload = {"subject": "temp", "value": [1, {"n": 2}]}
        record = Record(
            id="r2",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload=payload,
            signature="sig:r2",
        )
        payload["value"][1]["n"] = 999
        payload["value"].append(3)
        payload["subject"] = "changed"

        self.assertEqual(record.payload["subject"], "temp")
        self.assertEqual(record.payload["value"], (1, {"n": 2}))

    def test_record_create_uses_content_derived_id_when_not_provided(self) -> None:
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = Record.create(
            primitive_type=PrimitiveType.OBSERVATION,
            author="alice",
            schema="trs.observation.v1",
            payload={"subject": "temp", "value": 22, "meta": {"b": 2, "a": 1}},
            timestamp=timestamp,
            signature="sig:any",
        )
        second = Record.create(
            primitive_type=PrimitiveType.OBSERVATION,
            author="alice",
            schema="trs.observation.v1",
            payload={"meta": {"a": 1, "b": 2}, "value": 22, "subject": "temp"},
            timestamp=timestamp,
            signature="sig:different",
        )
        self.assertTrue(first.id.startswith("sha256:"))
        self.assertEqual(first.id, second.id)

    def test_record_create_keeps_explicit_id_for_compatibility(self) -> None:
        record = Record.create(
            primitive_type=PrimitiveType.OBSERVATION,
            author="alice",
            schema="trs.observation.v1",
            payload={"subject": "temp", "value": 1},
            record_id="legacy-id",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            signature="sig:legacy",
        )
        self.assertEqual(record.id, "legacy-id")


if __name__ == "__main__":
    unittest.main()
