from __future__ import annotations

from datetime import datetime, timezone
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest

from trs import Client, TRSConnectionError, TRSValidationError


def _record(record_id: str, primitive: str = "Observation", causes: list[str] | None = None) -> dict:
    payload_by_type = {
        "Observation": {"subject": "stock", "value": 1},
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


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _make_handler(delay_seconds: float = 0.0):
    class Handler(BaseHTTPRequestHandler):
        records: dict[str, dict] = {}

        def _json(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionAbortedError):  # timeout tests may close client socket first
                return

        def log_message(self, _format: str, *_args) -> None:  # pragma: no cover
            return

        def do_GET(self) -> None:
            if delay_seconds:
                time.sleep(delay_seconds)
            if self.path == "/health":
                self._json(200, {"status": "ok", "runtime": "1.0.0", "node": "0.1.0"})
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if delay_seconds:
                time.sleep(delay_seconds)
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw.decode("utf-8"))

            if self.path == "/submit":
                record = payload.get("record")
                if not isinstance(record, dict):
                    self._json(422, {"detail": "field 'record' must be an object"})
                    return
                if not isinstance(record.get("payload"), dict):
                    self._json(200, {"accepted": False, "record_id": record.get("id", ""), "errors": ["5.3 Payload Shape"]})
                    return
                primitive = str(record.get("type", ""))
                record_payload = record["payload"]
                required = {
                    "Observation": ("subject", "value"),
                    "Intention": ("goal", "horizon"),
                    "Commitment": ("action", "due_by"),
                }.get(primitive, ())
                if any(key not in record_payload for key in required):
                    self._json(200, {"accepted": False, "record_id": record.get("id", ""), "errors": ["5.3 Payload Shape"]})
                    return
                Handler.records[str(record["id"])] = record
                self._json(200, {"accepted": True, "record_id": str(record["id"]), "errors": []})
                return

            if self.path == "/query":
                query = payload.get("query", {})
                if not isinstance(query, dict):
                    self._json(422, {"detail": "field 'query' must be an object"})
                    return
                rows = list(Handler.records.values())
                if "type" in query:
                    rows = [row for row in rows if row.get("type") == query["type"]]
                self._json(200, {"records": rows})
                return

            if self.path == "/sync":
                records = payload.get("records", [])
                if not isinstance(records, list):
                    self._json(422, {"detail": "field 'records' must be an array"})
                    return
                accepted = 0
                appended_ids: list[str] = []
                for record in records:
                    if isinstance(record, dict) and "id" in record:
                        Handler.records[str(record["id"])] = record
                        accepted += 1
                        appended_ids.append(str(record["id"]))
                self._json(
                    200,
                    {
                        "accepted_count": accepted,
                        "rejected_count": 0,
                        "appended_ids": appended_ids,
                        "rejected_errors": [],
                    },
                )
                return

            if self.path == "/replay":
                self._json(
                    200,
                    {
                        "identities": {},
                        "workflows": {},
                        "contracts": {},
                        "reputation": {},
                        "coordination": {"unresolved_intentions": []},
                    },
                )
                return

            self._json(404, {"error": "not found"})

    return Handler


class _ServerHandle:
    def __init__(self, delay_seconds: float = 0.0) -> None:
        handler = _make_handler(delay_seconds)
        self.port = _free_port()
        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2.0)


class ClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = _ServerHandle()
        self.client = Client(f"http://127.0.0.1:{self.server.port}")

    def tearDown(self) -> None:
        self.server.stop()

    def test_health(self) -> None:
        health = self.client.health()
        self.assertEqual(health.status, "ok")
        self.assertEqual(health.runtime, "1.0.0")

    def test_submit_valid_record(self) -> None:
        result = self.client.submit(_record("g1"))
        self.assertTrue(result.accepted)
        self.assertEqual(result.record_id, "g1")

    def test_submit_invalid_record_raises_validation_error(self) -> None:
        bad = _record("bad1")
        bad["payload"] = {"wrong": 1}
        with self.assertRaises(TRSValidationError):
            self.client.submit(bad)

    def test_query_returns_expected_records(self) -> None:
        self.client.submit(_record("g1", "Observation"))
        self.client.submit(_record("i1", "Intention", causes=["g1"]))
        records = self.client.query({"type": "Intention"})
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], "i1")

    def test_replay_returns_state(self) -> None:
        replay = self.client.replay()
        self.assertIn("coordination", replay)

    def test_sync_between_two_nodes(self) -> None:
        other_server = _ServerHandle()
        try:
            other_client = Client(f"http://127.0.0.1:{other_server.port}")
            self.client.submit(_record("g1", "Observation"))
            self.client.submit(_record("i1", "Intention", causes=["g1"]))
            records = self.client.query({})
            sync_result = other_client.sync(records)
            self.assertEqual(sync_result.accepted_count, 2)
            mirrored = other_client.query({})
            self.assertEqual({r["id"] for r in mirrored}, {"g1", "i1"})
        finally:
            other_server.stop()

    def test_timeout_raises_connection_error(self) -> None:
        self.server.stop()
        slow_server = _ServerHandle(delay_seconds=0.25)
        try:
            client = Client(f"http://127.0.0.1:{slow_server.port}", timeout_seconds=0.05)
            with self.assertRaises(TRSConnectionError):
                client.health()
        finally:
            slow_server.stop()


if __name__ == "__main__":
    unittest.main()
