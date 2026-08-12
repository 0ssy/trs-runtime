from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class ReportedAuthorizationRegressionTests(unittest.TestCase):
    def test_unauthorized_alice_claim_without_authorization_is_rejected(self) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        task_root = Record(
            id="task-root",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "task", "value": {"task_id": "t-1", "status": "open"}},
            authorization=("task-root",),
            signature="sig:task-root",
        )
        store.append(task_root)
        bob_capability = Record(
            id="cap-bob",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate-completion-claim", "due_by": "2027-01-01", "assignee": "bob"},
            causes=("task-root",),
            authorization=("task-root",),
            signature="sig:cap-bob",
        )
        store.append(bob_capability)

        alice_claim = Record(
            id="alice-claim-complete",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "claim-completed", "due_by": "2027-01-01"},
            causes=("task-root",),
            signature="sig:alice-claim-complete",
        )
        result = verifier.verify(alice_claim)
        auth_rule = next(r for r in result.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.FAIL)

    def test_rootless_record_cannot_be_used_as_trust_root(self) -> None:
        store = RecordStore()
        verifier = Verifier(store)
        rootless = Record(
            id="rootless",
            type=PrimitiveType.OBSERVATION,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "rootless", "value": 1},
            signature="sig:rootless",
        )
        store.append(rootless)
        delegated = Record(
            id="delegated",
            type=PrimitiveType.COMMITMENT,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate", "due_by": "2027-01-01"},
            causes=("rootless",),
            authorization=("rootless",),
            signature="sig:delegated",
        )
        result = verifier.verify(delegated)
        auth_rule = next(r for r in result.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.FAIL)
        self.assertIn("trust root", auth_rule.reason)


if __name__ == "__main__":
    unittest.main()
