from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class SchemaTests(unittest.TestCase):
    def test_duplicate_id_fails_immutability_rule(self) -> None:
        store = RecordStore()
        verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
        record = Record(
            id="dup",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "s", "value": 1},
            signature="sig:dup",
        )
        store.append(record)
        result = verifier.verify(record)
        immutability = next(r for r in result.rules if r.rule_id == "4.1")
        self.assertEqual(immutability.status, RuleStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
