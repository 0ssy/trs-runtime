from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class VerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = RecordStore()
        self.verifier = Verifier(self.store)
        self.genesis = Record(
            id="genesis",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "root", "value": 1},
            signature="sig:genesis",
        )
        self.store.append(self.genesis)

    def test_declared_primitive_controls_payload_validation(self) -> None:
        record = Record(
            id="obs-bad",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"action": "ship", "due_by": "2027-01-01"},
            signature="sig:obs-bad",
        )
        result = self.verifier.verify(record)
        payload_rule = next(r for r in result.rules if r.rule_id == "5.3")
        self.assertEqual(payload_rule.status, RuleStatus.FAIL)
        self.assertFalse(result.valid)

    def test_causality_fails_when_cause_missing(self) -> None:
        record = Record(
            id="r2",
            type=PrimitiveType.INTENTION,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "launch", "horizon": "Q1"},
            causes=("missing",),
            signature="sig:r2",
        )
        result = self.verifier.verify(record)
        self.assertFalse(result.valid)
        self.assertTrue(any("missing causes" in err for err in result.errors))

    def test_authorization_trace_passes_with_path(self) -> None:
        delegation = Record(
            id="delegation",
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate", "due_by": "2026-12-31"},
            authorization=("genesis",),
            signature="sig:delegation",
        )
        self.store.append(delegation)
        record = Record(
            id="work",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "execute", "due_by": "2027-01-01"},
            authorization=("delegation",),
            signature="sig:work",
        )
        result = self.verifier.verify(record)
        auth_rule = next(r for r in result.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.PASS)
        self.assertEqual(result.authorization_path, ["delegation", "genesis"])


if __name__ == "__main__":
    unittest.main()
