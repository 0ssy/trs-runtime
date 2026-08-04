from __future__ import annotations

from dataclasses import dataclass, field
import io
import json
import tempfile
import unittest
from unittest.mock import patch

from trs import TRSConnectionError, TRSValidationError
from trs_cli.main import run


@dataclass(frozen=True)
class _Health:
    status: str = "ok"
    runtime: str = "1.0.0"
    node: str = "0.1.0"


@dataclass(frozen=True)
class _Submit:
    accepted: bool = True
    record_id: str = "g1"
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _Sync:
    accepted_count: int = 1
    rejected_count: int = 0
    appended_ids: list[str] = field(default_factory=lambda: ["g1"])
    rejected_errors: list[list[str]] = field(default_factory=list)


class _FakeClient:
    def __init__(self, _url: str, *, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    def health(self) -> _Health:
        return _Health()

    def submit(self, record: dict) -> _Submit:
        if record.get("id") == "bad":
            raise TRSValidationError("record rejected by verifier", errors=["5.3 Payload Shape"])
        return _Submit(record_id=str(record.get("id", "g1")))

    def query(self, _expr: dict) -> list[dict]:
        return [{"id": "i1", "type": "Intention"}]

    def sync(self, records: list[dict]) -> _Sync:
        return _Sync(accepted_count=len(records), appended_ids=[str(r.get("id", "")) for r in records])

    def replay(self) -> dict:
        return {"coordination": {"unresolved_intentions": []}}


class _ErrorClient(_FakeClient):
    def health(self) -> _Health:
        raise TRSConnectionError("timed out")


class CliTests(unittest.TestCase):
    @patch("trs_cli.main.Client", _FakeClient)
    def test_health(self) -> None:
        out = io.StringIO()
        with patch("sys.stdout", out):
            code = run(["health"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["status"], "ok")

    @patch("trs_cli.main.Client", _FakeClient)
    def test_submit_with_inline_json(self) -> None:
        out = io.StringIO()
        with patch("sys.stdout", out):
            code = run(["submit", "--record-json", "{\"id\":\"g1\"}"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out.getvalue())["accepted"])

    @patch("trs_cli.main.Client", _FakeClient)
    def test_submit_validation_error_exit_code(self) -> None:
        err = io.StringIO()
        with patch("sys.stderr", err):
            code = run(["submit", "--record-json", "{\"id\":\"bad\"}"])
        self.assertEqual(code, 2)
        self.assertIn("record rejected", err.getvalue())

    @patch("trs_cli.main.Client", _FakeClient)
    def test_query_returns_records(self) -> None:
        out = io.StringIO()
        with patch("sys.stdout", out):
            code = run(["query", "--expr-json", "{}"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["records"][0]["id"], "i1")

    @patch("trs_cli.main.Client", _FakeClient)
    def test_replay_returns_state(self) -> None:
        out = io.StringIO()
        with patch("sys.stdout", out):
            code = run(["replay"])
        self.assertEqual(code, 0)
        self.assertIn("coordination", json.loads(out.getvalue()))

    @patch("trs_cli.main.Client", _FakeClient)
    def test_sync_from_file(self) -> None:
        with tempfile.NamedTemporaryFile("w+", suffix=".json", encoding="utf-8", delete=False) as handle:
            json.dump([{"id": "g1"}, {"id": "i1"}], handle)
            path = handle.name
        out = io.StringIO()
        with patch("sys.stdout", out):
            code = run(["sync", "--records-file", path])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["accepted_count"], 2)

    @patch("trs_cli.main.Client", _ErrorClient)
    def test_connection_timeout_exit_code(self) -> None:
        err = io.StringIO()
        with patch("sys.stderr", err):
            code = run(["health"])
        self.assertEqual(code, 1)
        self.assertIn("timed out", err.getvalue())


if __name__ == "__main__":
    unittest.main()
