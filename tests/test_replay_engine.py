from __future__ import annotations

from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.replay import ReplayEngine
from runtime.storage import RecordStore


class ReplayEngineTests(unittest.TestCase):
    def test_replay_rebuilds_views_from_append_only_log(self) -> None:
        store = RecordStore()
        g = Record(
            id="g",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "boot", "value": 1},
            signature="sig:g",
        )
        i1 = Record(
            id="i1",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "ship", "horizon": "Q1"},
            causes=("g",),
            signature="sig:i1",
        )
        c1 = Record(
            id="c1",
            type=PrimitiveType.COMMITMENT,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "deliver", "due_by": "2026-12-31"},
            causes=("i1",),
            authorization=("g",),
            signature="sig:c1",
        )
        c2 = Record(
            id="c2",
            type=PrimitiveType.COMMITMENT,
            author="carol",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "audit", "due_by": "2026-12-31"},
            causes=("g",),
            authorization=("g",),
            signature="sig:c2",
        )
        i2 = Record(
            id="i2",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "review", "horizon": "Q2"},
            causes=("g",),
            signature="sig:i2",
        )
        for record in (g, i1, c1, c2, i2):
            store.append(record)

        snapshot = ReplayEngine(store).replay()

        self.assertEqual(snapshot.identities["alice"], ["i1", "i2"])
        self.assertEqual(set(snapshot.workflows["g"]), {"i1", "i2", "c1", "c2"})
        self.assertEqual(snapshot.contracts, ["c1", "c2"])
        self.assertEqual(snapshot.reputation["alice"], 2)
        self.assertEqual(snapshot.coordination.intention_to_commitments["i1"], ["c1"])
        self.assertEqual(snapshot.coordination.intention_to_commitments["i2"], [])
        self.assertEqual(snapshot.coordination.unresolved_intentions, ["i2"])
        self.assertEqual(snapshot.coordination.orphan_commitments, ["c2"])


if __name__ == "__main__":
    unittest.main()
