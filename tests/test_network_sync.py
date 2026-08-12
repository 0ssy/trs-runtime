from __future__ import annotations

from datetime import datetime, timezone
import unittest

from runtime.network_sync import ingest_records_unordered, sync_nodes
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


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

    def test_partition_divergent_subject_chains_surface_conflict_on_reconnect(self) -> None:
        shared_root = Record(
            id="g-partition",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "task-42", "value": "created"},
            authorization=("g-partition",),
            signature="sig:g-partition",
        )

        node_a = RecordStore()
        node_b = RecordStore()
        node_a.append(shared_root)
        node_b.append(shared_root)

        a1 = Record(
            id="a1",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "claim-progress", "due_by": "2027-01-01", "value": "in-progress"},
            causes=("g-partition",),
            authorization=("g-partition",),
            subject="task-42",
            signature="sig:a1",
        )
        a2 = Record(
            id="a2",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "claim-progress", "due_by": "2027-01-01", "value": "done"},
            causes=("a1",),
            authorization=("g-partition",),
            subject="task-42",
            signature="sig:a2",
        )
        b1 = Record(
            id="b1",
            type=PrimitiveType.COMMITMENT,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "claim-progress", "due_by": "2027-01-01", "value": "in-progress"},
            causes=("g-partition",),
            authorization=("g-partition",),
            subject="task-42",
            signature="sig:b1",
        )
        b2 = Record(
            id="b2",
            type=PrimitiveType.COMMITMENT,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "claim-progress", "due_by": "2027-01-01", "value": "blocked"},
            causes=("b1",),
            authorization=("g-partition",),
            subject="task-42",
            signature="sig:b2",
        )
        for record in (a1, a2):
            node_a.append(record)
        for record in (b1, b2):
            node_b.append(record)

        result = sync_nodes(node_b, node_a, Verifier(node_a))
        self.assertEqual(result.rejected_ids, [])
        self.assertIn("b2", result.appended_ids)
        b2_verification = next(v for rid, v in zip(result.appended_ids, result.verification_results) if rid == "b2")
        conflict_rule = next(r for r in b2_verification.rules if r.rule_id == "4.5")
        self.assertEqual(conflict_rule.status, RuleStatus.PASS)
        self.assertIn("a2", conflict_rule.reason)


if __name__ == "__main__":
    unittest.main()
