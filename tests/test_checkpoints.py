from datetime import datetime, timedelta, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.sync import build_checkpoint_record
from runtime.verifier import RuleStatus, Verifier


class CheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = RecordStore()
        self.verifier = Verifier(self.store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
        self.genesis = Record(
            id="g-check",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "boot", "value": 1},
            authorization=("g-check",),
            signature="sig:g-check",
        )
        self.store.append(self.genesis)

    def test_build_checkpoint_record_contains_inventory_and_heads(self) -> None:
        checkpoint = build_checkpoint_record(
            self.store,
            author="root",
            timestamp=datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc),
            signature="sig:checkpoint",
        )
        self.assertEqual(checkpoint.type, PrimitiveType.OBSERVATION)
        self.assertEqual(checkpoint.payload["subject"], "trs.checkpoint")
        self.assertIn("inventory_hash", checkpoint.payload["value"])
        self.assertEqual(checkpoint.payload["value"]["heads"], ("g-check",))
        self.assertEqual(checkpoint.causes, ("g-check",))

    def test_backdated_record_fails_when_checkpoint_exists(self) -> None:
        checkpoint = build_checkpoint_record(
            self.store,
            author="root",
            timestamp=datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc),
            signature="sig:checkpoint",
            record_id="cp1",
        )
        self.assertTrue(self.verifier.verify(checkpoint).valid)
        self.store.append(checkpoint)

        backdated = Record(
            id="late-old",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=checkpoint.timestamp - timedelta(minutes=5),
            schema="trs.commitment.v1",
            payload={"action": "execute", "due_by": "2027-01-01"},
            causes=("g-check",),
            authorization=("g-check",),
            signature="sig:late-old",
        )
        result = self.verifier.verify(backdated)
        self.assertFalse(result.valid)
        checkpoint_rule = next(rule for rule in result.rules if rule.rule_id == "5.4")
        self.assertEqual(checkpoint_rule.status, RuleStatus.FAIL)
        self.assertIn("latest checkpoint", checkpoint_rule.reason)

    def test_newer_record_passes_after_checkpoint(self) -> None:
        checkpoint = build_checkpoint_record(
            self.store,
            author="root",
            timestamp=datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc),
            signature="sig:checkpoint",
            record_id="cp2",
        )
        self.assertTrue(self.verifier.verify(checkpoint).valid)
        self.store.append(checkpoint)

        newer = Record(
            id="newer",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=checkpoint.timestamp + timedelta(minutes=5),
            schema="trs.commitment.v1",
            payload={"action": "execute", "due_by": "2027-01-01"},
            causes=("g-check",),
            authorization=("g-check",),
            signature="sig:newer",
        )
        result = self.verifier.verify(newer)
        self.assertTrue(result.valid)
        checkpoint_rule = next(rule for rule in result.rules if rule.rule_id == "5.4")
        self.assertEqual(checkpoint_rule.status, RuleStatus.PASS)


if __name__ == "__main__":
    unittest.main()
