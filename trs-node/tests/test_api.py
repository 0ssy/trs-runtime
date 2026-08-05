from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from node.runtime_service import RuntimeService
from node.server import create_app
from runtime.storage import SQLiteStorage


def _record(record_id: str, *, primitive: str = "Observation", causes: list[str] | None = None) -> dict:
    payload_by_type = {
        "Observation": {"subject": "boot", "value": 1},
        "Intention": {"goal": "allocate", "horizon": "today"},
        "Commitment": {"action": "deliver", "due_by": "2027-01-01"},
    }
    schema_by_type = {
        "Observation": "trs.observation.v1",
        "Intention": "trs.intention.v1",
        "Commitment": "trs.commitment.v1",
    }
    return {
        "id": record_id,
        "type": primitive,
        "author": "tester",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema": schema_by_type[primitive],
        "payload": payload_by_type[primitive],
        "causes": causes or [],
        "authorization": [],
        "signature": f"sig:{record_id}",
    }


class NodeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["runtime"], "1.0.0")
        self.assertEqual(body["node"], "0.1.0")

    def test_submit_valid_record(self) -> None:
        response = self.client.post("/submit", json={"record": _record("g1")})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["accepted"])
        self.assertEqual(body["record_id"], "g1")
        self.assertEqual(body["errors"], [])

    def test_submit_invalid_record(self) -> None:
        invalid = _record("bad1")
        invalid["payload"] = {"wrong": "shape"}
        response = self.client.post("/submit", json={"record": invalid})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["accepted"])
        self.assertTrue(any("5.3 Payload Shape" in error for error in body["errors"]))

    def test_get_record_by_id(self) -> None:
        self.client.post("/submit", json={"record": _record("g1")})
        response = self.client.get("/record/g1")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["id"], "g1")
        self.assertEqual(body["type"], "Observation")

    def test_get_record_by_id_not_found(self) -> None:
        response = self.client.get("/record/missing")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_query_round_trip(self) -> None:
        self.client.post("/submit", json={"record": _record("g1")})
        self.client.post("/submit", json={"record": _record("i1", primitive="Intention", causes=["g1"])})

        response = self.client.post("/query", json={"query": {"type": "Intention"}})
        self.assertEqual(response.status_code, 200)
        records = response.json()["records"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], "i1")

    def test_replay_reconstructs_state(self) -> None:
        self.client.post("/submit", json={"record": _record("g1")})
        self.client.post("/submit", json={"record": _record("i1", primitive="Intention", causes=["g1"])})

        response = self.client.post("/replay")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("coordination", body)
        self.assertIn("unresolved_intentions", body["coordination"])

    def test_sync_appends_to_target_node(self) -> None:
        source = TestClient(create_app())
        target = TestClient(create_app())

        source.post("/submit", json={"record": _record("g1")})
        source.post("/submit", json={"record": _record("i1", primitive="Intention", causes=["g1"])})

        source_records = source.post("/query", json={"query": {}}).json()["records"]
        sync_response = target.post("/sync", json={"records": source_records})
        self.assertEqual(sync_response.status_code, 200)
        body = sync_response.json()
        self.assertEqual(body["accepted_count"], 2)
        self.assertEqual(body["rejected_count"], 0)

        target_records = target.post("/query", json={"query": {}}).json()["records"]
        self.assertEqual({record["id"] for record in target_records}, {"g1", "i1"})

    def test_sqlite_serve_profile_persists_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trs-node.db")
            first_client = TestClient(create_app(service=RuntimeService(store=SQLiteStorage(db_path))))
            submit_response = first_client.post("/submit", json={"record": _record("g1")})
            self.assertEqual(submit_response.status_code, 200)
            self.assertTrue(submit_response.json()["accepted"])
            first_client.close()

            second_client = TestClient(create_app(service=RuntimeService(store=SQLiteStorage(db_path))))
            query_response = second_client.post("/query", json={"query": {}})
            self.assertEqual(query_response.status_code, 200)
            records = query_response.json()["records"]
            self.assertEqual([record["id"] for record in records], ["g1"])
            second_client.close()


if __name__ == "__main__":
    unittest.main()
