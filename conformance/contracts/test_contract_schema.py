from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class ContractTests(unittest.TestCase):
    def test_commitment_schema_must_match_declared_primitive(self) -> None:
        store = RecordStore()
        verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
        record = Record(
            id="contract-1",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"action": "pay", "due_by": "2026-09-01"},
            signature="sig:contract-1",
        )
        result = verifier.verify(record)
        schema_rule = next(r for r in result.rules if r.rule_id == "5.1")
        self.assertEqual(schema_rule.status, RuleStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
