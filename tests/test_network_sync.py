from __future__ import annotations

from datetime import datetime, timezone
import unittest

from runtime.network_sync import ingest_records_unordered, sync_nodes
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import Verifier


class NetworkSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = RecordStore()
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
            self.source.append(record)

    def test_ingest_records_unordered_handles_dependency_retries(self) -> None:
        target = RecordStore()
        verifier = Verifier(target)
        result = ingest_records_unordered(target, [self.b, self.a, self.g], verifier)
        self.assertEqual(set(result.appended_ids), {"g", "a", "b"})
        self.assertEqual(result.rejected_ids, [])
        self.assertEqual([r.id for r in target.all()], ["g", "a", "b"])

    def test_sync_nodes_exchanges_inventory_and_appends_missing(self) -> None:
        target = RecordStore()
        target_verifier = Verifier(target)
        before_source = [r.id for r in self.source.all()]
        result = sync_nodes(self.source, target, target_verifier)
        self.assertEqual(set(result.missing_ids), {"g", "a", "b"})
        self.assertEqual(set(result.appended_ids), {"g", "a", "b"})
        self.assertEqual(result.rejected_ids, [])
        self.assertEqual([r.id for r in target.all()], ["g", "a", "b"])
        self.assertEqual([r.id for r in self.source.all()], before_source)


if __name__ == "__main__":
    unittest.main()
