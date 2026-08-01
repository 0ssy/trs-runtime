from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import shutil
import tempfile
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import LMDBStorage


@unittest.skipUnless(importlib.util.find_spec("lmdb") is not None, "lmdb package not installed")
class LMDBStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir_path = tempfile.mkdtemp(prefix="trs-runtime-lmdb-")
        self._stores: list[LMDBStorage] = []

    def tearDown(self) -> None:
        for store in self._stores:
            store.close()
        shutil.rmtree(self.dir_path, ignore_errors=True)

    def _new_store(self) -> LMDBStorage:
        store = LMDBStorage(self.dir_path)
        self._stores.append(store)
        return store

    def test_append_get_exists_children_all_and_query(self) -> None:
        store = self._new_store()
        root = Record(
            id="g1",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "state", "value": 1},
            signature="sig:g1",
        )
        child = Record(
            id="c1",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "ship", "horizon": "Q1"},
            causes=("g1",),
            signature="sig:c1",
        )

        store.append(root)
        store.append(child)

        self.assertTrue(store.exists("g1"))
        loaded_child = store.get("c1")
        self.assertIsNotNone(loaded_child)
        self.assertEqual(loaded_child.id, "c1")
        self.assertEqual([r.id for r in store.children("g1")], ["c1"])
        self.assertEqual(store.parents("c1"), ["g1"])
        self.assertEqual([r.id for r in store.all()], ["g1", "c1"])
        self.assertEqual([r.id for r in store.query({"author": "alice"})], ["c1"])

    def test_persists_across_instances(self) -> None:
        first = self._new_store()
        record = Record(
            id="r1",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "x", "value": 1},
            signature="sig:r1",
        )
        first.append(record)
        first.close()

        second = self._new_store()
        self.assertTrue(second.exists("r1"))
        loaded = second.get("r1")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, "r1")


if __name__ == "__main__":
    unittest.main()
