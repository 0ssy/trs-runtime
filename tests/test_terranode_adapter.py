from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.terranode_adapter import TerraNodeRuntimeAdapter


class TerraNodeAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = TerraNodeRuntimeAdapter(
            allow_insecure_signatures=True,
            enforce_canonical_record_id=False,
        )
        genesis = {
            "id": "g1",
            "type": "Observation",
            "author": "root",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema": "trs.observation.v1",
            "payload": {"subject": "boot", "value": 1},
            "authorization": ["g1"],
            "signature": "sig:g1",
        }
        result = self.adapter.submit_envelope(genesis)
        self.assertTrue(result.accepted)

    def test_submit_envelope_verifies_and_appends(self) -> None:
        envelope = {
            "id": "i1",
            "type": "Intention",
            "author": "alice",
            "timestamp": datetime.now(timezone.utc),
            "schema": "trs.intention.v1",
            "payload": {"goal": "launch", "horizon": "Q1"},
            "causes": ["g1"],
            "signature": "sig:i1",
        }
        result = self.adapter.submit_envelope(envelope)
        self.assertTrue(result.accepted)
        self.assertIsNotNone(self.adapter.get_record("i1"))

    def test_submit_rejects_invalid_envelope(self) -> None:
        envelope = {
            "id": "bad",
            "type": "Observation",
            "author": "mallory",
            "timestamp": datetime.now(timezone.utc),
            "schema": "trs.observation.v1",
            "payload": {"action": "forge", "due_by": "2027-01-01"},
            "signature": "sig:bad",
        }
        result = self.adapter.submit_envelope(envelope)
        self.assertFalse(result.accepted)
        self.assertIsNone(self.adapter.get_record("bad"))

    def test_sync_incoming_uses_runtime_verifier(self) -> None:
        incoming = [
            Record(
                id="c1",
                type=PrimitiveType.COMMITMENT,
                author="alice",
                timestamp=datetime.now(timezone.utc),
                schema="trs.commitment.v1",
                payload={"action": "deliver", "due_by": "2026-12-31"},
                causes=("g1",),
                authorization=("g1",),
                signature="sig:c1",
            )
        ]
        result = self.adapter.sync_incoming(incoming)
        self.assertEqual(result.appended_ids, ["c1"])


if __name__ == "__main__":
    unittest.main()
