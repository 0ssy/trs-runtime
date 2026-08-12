from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class VerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = RecordStore()
        self.verifier = Verifier(self.store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
        self.genesis = Record(
            id="genesis",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "root", "value": 1},
            authorization=("genesis",),
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

    def test_rootless_record_is_not_trust_root(self) -> None:
        rootless = Record(
            id="rootless",
            type=PrimitiveType.OBSERVATION,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "rootless", "value": 1},
            signature="sig:rootless",
        )
        self.store.append(rootless)
        delegation = Record(
            id="delegation-rootless",
            type=PrimitiveType.COMMITMENT,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate", "due_by": "2027-01-01"},
            causes=("rootless",),
            authorization=("rootless",),
            signature="sig:delegation-rootless",
        )
        result = self.verifier.verify(delegation)
        self.assertFalse(result.valid)
        self.assertTrue(any("trust root" in err for err in result.errors))

    def test_unauthorized_alice_completion_claim_fails(self) -> None:
        delegation = Record(
            id="cap-bob",
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate-completion-claim", "due_by": "2027-01-01", "assignee": "bob"},
            causes=("genesis",),
            authorization=("genesis",),
            signature="sig:cap-bob",
        )
        self.store.append(delegation)

        alice_claim = Record(
            id="claim-alice",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "claim-completed", "due_by": "2027-01-01"},
            causes=("genesis",),
            signature="sig:claim-alice",
        )
        result = self.verifier.verify(alice_claim)
        auth_rule = next(r for r in result.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.FAIL)
        self.assertIn("requires at least one authorization reference", auth_rule.reason)

    def test_commitment_without_authorization_fails(self) -> None:
        record = Record(
            id="c-no-auth",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "execute", "due_by": "2027-01-01"},
            causes=("genesis",),
            signature="sig:c-no-auth",
        )
        result = self.verifier.verify(record)
        self.assertFalse(result.valid)
        auth_rule = next(r for r in result.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.FAIL)
        self.assertIn("commitment requires", auth_rule.reason)

    def test_non_silent_conflict_cache_invalidates_on_append(self) -> None:
        candidate = Record(
            id="candidate",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "ship", "horizon": "Q1"},
            causes=("genesis",),
            signature="sig:candidate",
        )

        first = self.verifier.verify(candidate)
        first_rule = next(r for r in first.rules if r.rule_id == "4.5")
        self.assertEqual(first_rule.status, RuleStatus.NOT_APPLICABLE)

        sibling = Record(
            id="sibling",
            type=PrimitiveType.INTENTION,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "review", "horizon": "Q2"},
            causes=("genesis",),
            signature="sig:sibling",
        )
        self.store.append(sibling)

        second = self.verifier.verify(candidate)
        second_rule = next(r for r in second.rules if r.rule_id == "4.5")
        self.assertEqual(second_rule.status, RuleStatus.PASS)
        self.assertIn("sibling", second_rule.reason)

    def test_verification_cache_invalidates_on_append(self) -> None:
        missing_cause_record = Record(
            id="pending-intention",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "ship", "horizon": "Q1"},
            causes=("future-cause",),
            signature="sig:pending-intention",
        )

        first = self.verifier.verify(missing_cause_record)
        self.assertFalse(first.valid)
        self.assertTrue(any("missing causes" in err for err in first.errors))

        future_cause = Record(
            id="future-cause",
            type=PrimitiveType.OBSERVATION,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "ready", "value": 1},
            causes=("genesis",),
            signature="sig:future-cause",
        )
        self.store.append(future_cause)

        second = self.verifier.verify(missing_cause_record)
        self.assertTrue(second.valid)

    def test_default_verifier_rejects_non_canonical_id(self) -> None:
        strict_verifier = Verifier(self.store)
        record = Record(
            id="totally-made-up-id-not-a-hash",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "execute", "due_by": "2027-01-01"},
            causes=("genesis",),
            authorization=("genesis",),
            signature="ed25519:any:any",
        )
        result = strict_verifier.verify(record)
        identity_rule = next(r for r in result.rules if r.rule_id == "5.0")
        self.assertEqual(identity_rule.status, RuleStatus.FAIL)

    def test_default_verifier_rejects_stub_signature_without_crypto(self) -> None:
        strict_verifier = Verifier(self.store)
        record = Record(
            id="sha256:stub",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "x", "value": 1},
            signature="sig:stub",
        )
        result = strict_verifier.verify(record)
        signature_rule = next(r for r in result.rules if r.rule_id == "5.2")
        self.assertEqual(signature_rule.status, RuleStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
