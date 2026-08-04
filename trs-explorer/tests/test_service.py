from __future__ import annotations

import unittest

from trs_explorer.service import ExplorerService


class _FakeHealth:
    status = "ok"
    runtime = "1.0.0"
    node = "0.1.0"


class _FakeClient:
    def health(self):
        return _FakeHealth()

    def query(self, _expr):
        return [
            {
                "id": "g1",
                "type": "Observation",
                "author": "root",
                "subject": "boot",
                "schema": "trs.observation.v1",
                "timestamp": "2026-08-04T09:10:00+00:00",
                "causes": [],
                "authorization": [],
            },
            {
                "id": "i1",
                "type": "Intention",
                "author": "alice",
                "subject": "warehouse-7",
                "schema": "trs.intention.v1",
                "timestamp": "2026-08-04T09:15:00+00:00",
                "causes": ["g1"],
                "authorization": ["g1"],
            },
        ]

    def replay(self):
        return {"coordination": {"unresolved_intentions": ["i1"]}}

    def submit(self, _record):
        raise Exception("not used in this test")


class ServiceTests(unittest.TestCase):
    def test_graph_payload_builds_nodes_edges(self) -> None:
        service = ExplorerService(client=_FakeClient())
        payload = service.graph_payload()
        self.assertEqual(len(payload["nodes"]), 2)
        self.assertEqual(payload["edges"], [{"from": "g1", "to": "i1"}])
        intention = next(node for node in payload["nodes"] if node["id"] == "i1")
        self.assertEqual(intention["status"], "Open")


if __name__ == "__main__":
    unittest.main()

