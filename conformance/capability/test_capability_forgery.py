from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class CapabilityTests(unittest.TestCase):
    def test_missing_authorization_path_fails(self) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        forged = Record(
            id="forged",
            type=PrimitiveType.COMMITMENT,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "approve", "due_by": "2026-10-01"},
            authorization=("ghost",),
            signature="sig:forged",
        )
        result = verifier.verify(forged)
        auth_rule = next(r for r in result.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
