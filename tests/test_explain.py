from datetime import datetime, timezone
import unittest

from runtime.explain import explain
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import Verifier


class ExplainTests(unittest.TestCase):
    def test_explain_includes_rule_failures(self) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        record = Record(
            id="r",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "ship", "due_by": "2026-10-01"},
            authorization=("missing-auth",),
            signature="sig:r",
        )
        result = verifier.verify(record)
        text = explain(record, result, store)
        self.assertIn("Rule 6.1 Authorization Traceability: FAIL", text)
        self.assertIn("Valid: False", text)


if __name__ == "__main__":
    unittest.main()
