from __future__ import annotations

from datetime import datetime, timezone
import unittest

from hypothesis import given, settings, strategies as st

from runtime.explain import explain
from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.sync import sync_append_only
from runtime.verifier import Verifier


def _schema_for(primitive: PrimitiveType) -> str:
    return {
        PrimitiveType.OBSERVATION: "trs.observation.v1",
        PrimitiveType.COMMITMENT: "trs.commitment.v1",
        PrimitiveType.INTENTION: "trs.intention.v1",
    }[primitive]


def _payload_for(primitive: PrimitiveType, index: int) -> dict[str, object]:
    if primitive == PrimitiveType.OBSERVATION:
        return {"subject": f"s{index}", "value": index}
    if primitive == PrimitiveType.COMMITMENT:
        return {"action": f"act-{index}", "due_by": "2027-01-01"}
    return {"goal": f"goal-{index}", "horizon": "Q1"}


def _make_record(
    record_id: str, primitive: PrimitiveType, author: str, index: int, causes: tuple[str, ...] = ()
) -> Record:
    authorization: tuple[str, ...]
    if primitive == PrimitiveType.COMMITMENT:
        authorization = ("g0",)
    elif primitive == PrimitiveType.OBSERVATION and record_id == "g0":
        authorization = ("g0",)
    else:
        authorization = ()
    return Record(
        id=record_id,
        type=primitive,
        author=author,
        timestamp=datetime.now(timezone.utc),
        schema=_schema_for(primitive),
        payload=_payload_for(primitive, index),
        causes=causes,
        authorization=authorization,
        signature=f"sig:{record_id}",
    )


class PropertyInvariantTests(unittest.TestCase):
    @settings(max_examples=40, deadline=None)
    @given(
        primitive=st.sampled_from(list(PrimitiveType)),
        author=st.text(min_size=1, max_size=8, alphabet=st.characters(whitelist_categories=("Ll",))),
    )
    def test_duplicate_ids_are_never_accepted(self, primitive: PrimitiveType, author: str) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        first = _make_record("dup-id", primitive, author, 1)
        store.append(first)
        second = _make_record("dup-id", primitive, author, 2)
        result = verifier.verify(second)
        self.assertFalse(result.valid)
        self.assertTrue(any("4.1 Immutability" in err for err in result.errors))

    @settings(max_examples=35, deadline=None)
    @given(
        length=st.integers(min_value=3, max_value=25),
        query_author=st.text(min_size=1, max_size=8, alphabet=st.characters(whitelist_categories=("Ll",))),
    )
    def test_queries_never_mutate_storage(self, length: int, query_author: str) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        genesis = _make_record("g0", PrimitiveType.OBSERVATION, "root", 0)
        store.append(genesis)

        prev_id = "g0"
        for i in range(1, length):
            primitive = [PrimitiveType.OBSERVATION, PrimitiveType.INTENTION, PrimitiveType.COMMITMENT][i % 3]
            record = _make_record(f"r{i}", primitive, f"a{i % 4}", i, (prev_id,))
            result = verifier.verify(record)
            if result.valid:
                store.append(record)
                prev_id = record.id

        engine = QueryEngine(store)
        before_ids = [r.id for r in store.all()]
        _ = engine.query({"author": query_author})
        _ = engine.query({"type": PrimitiveType.INTENTION})
        after_ids = [r.id for r in store.all()]
        self.assertEqual(before_ids, after_ids)

    @settings(max_examples=30, deadline=None)
    @given(length=st.integers(min_value=2, max_value=20))
    def test_accepted_records_are_explainable(self, length: int) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        g = _make_record("g0", PrimitiveType.OBSERVATION, "root", 0)
        g_result = verifier.verify(g)
        self.assertTrue(g_result.valid)
        store.append(g)
        self.assertIn("Valid: True", explain(g, g_result, store))

        prev_id = "g0"
        for i in range(1, length):
            primitive = [PrimitiveType.OBSERVATION, PrimitiveType.INTENTION, PrimitiveType.COMMITMENT][i % 3]
            record = _make_record(f"r{i}", primitive, f"user{i % 5}", i, (prev_id,))
            result = verifier.verify(record)
            if result.valid:
                store.append(record)
                text = explain(record, result, store)
                self.assertIn("Valid: True", text)
                self.assertIn("Verification summary:", text)
                prev_id = record.id

    @settings(max_examples=30, deadline=None)
    @given(length=st.integers(min_value=3, max_value=20))
    def test_sync_never_mutates_existing_records(self, length: int) -> None:
        source = RecordStore()
        source_verifier = Verifier(source)
        g = _make_record("g0", PrimitiveType.OBSERVATION, "root", 0)
        source.append(g)
        prev_id = "g0"
        for i in range(1, length):
            primitive = [PrimitiveType.OBSERVATION, PrimitiveType.INTENTION, PrimitiveType.COMMITMENT][i % 3]
            record = _make_record(f"r{i}", primitive, f"user{i % 4}", i, (prev_id,))
            result = source_verifier.verify(record)
            if result.valid:
                source.append(record)
                prev_id = record.id

        local = RecordStore()
        local.append(g)
        local_snapshot = {r.id: r.to_dict() for r in local.all()}
        local_verifier = Verifier(local)
        result = sync_append_only(local, source.all(), local_verifier)
        self.assertGreaterEqual(len(result.appended_ids), 0)
        post_snapshot = {r.id: r.to_dict() for r in local.all() if r.id in local_snapshot}
        self.assertEqual(local_snapshot, post_snapshot)


if __name__ == "__main__":
    unittest.main()
