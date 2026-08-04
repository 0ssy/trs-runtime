from __future__ import annotations

import unittest

from trs_explorer.search import filter_records, parse_search


class SearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            {"id": "g1", "type": "Observation", "author": "alice", "subject": "warehouse-7", "schema": "trs.observation.v1"},
            {"id": "i1", "type": "Intention", "author": "alice", "subject": "warehouse-7", "schema": "trs.intention.v1"},
            {"id": "i2", "type": "Intention", "author": "bob", "subject": "warehouse-9", "schema": "trs.intention.v1"},
        ]

    def test_parse_search(self) -> None:
        parsed = parse_search("subject:warehouse-7 author:alice")
        self.assertEqual(parsed["subject"], "warehouse-7")
        self.assertEqual(parsed["author"], "alice")

    def test_filter_subject(self) -> None:
        out = filter_records(self.records, {"subject": "warehouse-7"})
        self.assertEqual({r["id"] for r in out}, {"g1", "i1"})

    def test_filter_open_status(self) -> None:
        out = filter_records(self.records, {"status": "open"}, unresolved_intentions={"i2"})
        self.assertEqual([r["id"] for r in out], ["i2"])


if __name__ == "__main__":
    unittest.main()

