from datetime import datetime, timezone
import unittest

from runtime.graph import Graph
from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


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

    def test_same_parent_different_subjects_are_not_conflict(self) -> None:
        store = RecordStore()
        verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
        root = Record(
            id="root2",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "state", "value": "open"},
            signature="sig:root2",
        )
        store.append(root)

        first = Record(
            id="i1",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "pick", "horizon": "Q1"},
            causes=("root2",),
            subject="warehouse-7/slot-a",
            signature="sig:i1",
        )
        store.append(first)

        second = Record(
            id="i2",
            type=PrimitiveType.INTENTION,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "pick", "horizon": "Q2"},
            causes=("root2",),
            subject="warehouse-7/slot-b",
            signature="sig:i2",
        )
        result = verifier.verify(second)
        conflict_rule = next(r for r in result.rules if r.rule_id == "4.5")
        self.assertEqual(conflict_rule.status, RuleStatus.NOT_APPLICABLE)

    def test_same_parent_same_subject_and_different_payload_is_conflict(self) -> None:
        store = RecordStore()
        verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
        root = Record(
            id="root3",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "state", "value": "open"},
            signature="sig:root3",
        )
        store.append(root)

        first = Record(
            id="i3",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "allocate", "horizon": "Q1"},
            causes=("root3",),
            subject="warehouse-7",
            signature="sig:i3",
        )
        store.append(first)

        second = Record(
            id="i4",
            type=PrimitiveType.INTENTION,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "allocate", "horizon": "Q2"},
            causes=("root3",),
            subject="warehouse-7",
            signature="sig:i4",
        )
        result = verifier.verify(second)
        conflict_rule = next(r for r in result.rules if r.rule_id == "4.5")
        self.assertEqual(conflict_rule.status, RuleStatus.PASS)

    def test_descendant_update_on_same_subject_is_not_conflict(self) -> None:
        store = RecordStore()
        verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
        root = Record(
            id="root4",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "state", "value": "open"},
            signature="sig:root4",
        )
        store.append(root)

        first = Record(
            id="i5",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "allocate", "horizon": "Q1"},
            causes=("root4",),
            subject="warehouse-8",
            signature="sig:i5",
        )
        store.append(first)

        second = Record(
            id="i6",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "allocate", "horizon": "Q2"},
            causes=("i5",),
            subject="warehouse-8",
            signature="sig:i6",
        )
        result = verifier.verify(second)
        conflict_rule = next(r for r in result.rules if r.rule_id == "4.5")
        self.assertEqual(conflict_rule.status, RuleStatus.NOT_APPLICABLE)


if __name__ == "__main__":
    unittest.main()
