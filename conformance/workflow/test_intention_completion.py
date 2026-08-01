from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import Verifier


class WorkflowCompletionTests(unittest.TestCase):
    def test_intention_requires_existing_cause_for_closure(self) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        intention = Record(
            id="i1",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "ship", "horizon": "Q1"},
            causes=("missing",),
            signature="sig:i1",
        )
        result = verifier.verify(intention)
        self.assertFalse(result.valid)
        self.assertTrue(any("missing causes" in e for e in result.errors))


if __name__ == "__main__":
    unittest.main()
