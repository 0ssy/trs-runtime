from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class WorkflowTests(unittest.TestCase):
    def test_genesis_without_causes_is_not_applicable_for_causality(self) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        genesis = Record(
            id="g",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "boot", "value": 1},
            signature="sig:g",
        )
        result = verifier.verify(genesis)
        causality = next(r for r in result.rules if r.rule_id == "4.2")
        self.assertEqual(causality.status, RuleStatus.NOT_APPLICABLE)


if __name__ == "__main__":
    unittest.main()
