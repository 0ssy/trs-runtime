from __future__ import annotations

from datetime import datetime, timezone
import json
import unittest

from runtime.canonical import canonical_record_bytes as canonical_record_bytes_with_signature
from runtime.crypto import CryptoSuite, clone_with_signature
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class CryptoPhase12Tests(unittest.TestCase):
    def test_signing_canonical_bytes_exclude_signature_field(self) -> None:
        record = Record(
            id="r-sign",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "temp", "value": 1},
            signature="ed25519:key:abc",
        )
        signing_bytes = canonical_record_bytes_with_signature(record, include_signature=False)
        parsed = json.loads(signing_bytes.decode("utf-8"))
        self.assertNotIn("signature", parsed)

    def test_signatures_verify_when_signature_value_changes(self) -> None:
        crypto = CryptoSuite()
        key = crypto.generate_key("alice")
        record = Record(
            id="r-sig-2",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "temp", "value": 1},
            signature="",
        )
        signature = crypto.sign_record(record, key.private_key_b64, key.key_id)
        signed = clone_with_signature(record, signature)
        ok, reason = crypto.verify_record_signature(signed)
        self.assertTrue(ok, reason)

        same_payload_different_signature = clone_with_signature(signed, f"ed25519:{key.key_id}:AAAA")
        ok2, reason2 = crypto.verify_record_signature(same_payload_different_signature)
        self.assertFalse(ok2)
        self.assertEqual(reason2, "signature verification failed")

    def test_canonicalization_is_deterministic_for_equivalent_payloads(self) -> None:
        timestamp = datetime.now(timezone.utc)
        left = Record(
            id="canon-1",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=timestamp,
            schema="trs.observation.v1",
            payload={"z": {"b": 2, "a": 1}, "subject": "s", "value": 1},
            signature="sig:left",
        )
        right = Record(
            id="canon-1",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=timestamp,
            schema="trs.observation.v1",
            payload={"subject": "s", "value": 1, "z": {"a": 1, "b": 2}},
            signature="sig:right",
        )
        self.assertEqual(
            canonical_record_bytes_with_signature(left, include_signature=False),
            canonical_record_bytes_with_signature(right, include_signature=False),
        )

    def test_ed25519_sign_and_verify(self) -> None:
        crypto = CryptoSuite()
        key = crypto.generate_key("alice")
        record = Record(
            id="r1",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "temp", "value": 1},
            signature="",
        )
        signed = clone_with_signature(record, crypto.sign_record(record, key.private_key_b64, key.key_id))
        ok, reason = crypto.verify_record_signature(signed)
        self.assertTrue(ok, reason)

        tampered = Record(
            id=signed.id,
            type=signed.type,
            author=signed.author,
            timestamp=signed.timestamp,
            schema=signed.schema,
            payload={"subject": "temp", "value": 999},
            causes=signed.causes,
            authorization=signed.authorization,
            signature=signed.signature,
        )
        ok2, _ = crypto.verify_record_signature(tampered)
        self.assertFalse(ok2)

    def test_key_rotation_still_verifies_previous_signatures(self) -> None:
        crypto = CryptoSuite()
        old_key = crypto.generate_key("alice")
        new_key = crypto.rotate_key("alice")
        self.assertNotEqual(old_key.key_id, new_key.key_id)

        old_record = Record(
            id="old",
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "old", "value": 1},
            signature="",
        )
        old_signed = clone_with_signature(
            old_record, crypto.sign_record(old_record, old_key.private_key_b64, old_key.key_id)
        )
        ok, reason = crypto.verify_record_signature(old_signed)
        self.assertTrue(ok, reason)

    def test_log_delegation_required_for_authorization_chain_when_crypto_enabled(self) -> None:
        store = RecordStore()
        crypto = CryptoSuite()
        root_key = crypto.generate_key("root")
        alice_key = crypto.generate_key("alice")
        verifier = Verifier(store, crypto=crypto)

        genesis = Record(
            id="g1",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "boot", "value": 1},
            authorization=("g1",),
            signature="",
        )
        genesis = clone_with_signature(genesis, crypto.sign_record(genesis, root_key.private_key_b64, root_key.key_id))
        self.assertTrue(verifier.verify(genesis).valid)
        store.append(genesis)

        capability = Record(
            id="cap1",
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "authorize-work", "due_by": "2027-01-01"},
            authorization=("g1",),
            signature="",
        )
        capability = clone_with_signature(
            capability, crypto.sign_record(capability, root_key.private_key_b64, root_key.key_id)
        )
        self.assertTrue(verifier.verify(capability).valid)
        store.append(capability)

        work = Record(
            id="work1",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "execute", "due_by": "2027-01-01"},
            authorization=("cap1",),
            signature="",
        )
        work = clone_with_signature(work, crypto.sign_record(work, alice_key.private_key_b64, alice_key.key_id))
        no_delegation = verifier.verify(work)
        auth_rule = next(r for r in no_delegation.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.FAIL)
        self.assertIn("missing log delegation", auth_rule.reason)

        delegation = Record(
            id="deleg1",
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate-authority", "due_by": "2027-01-01", "assignee": "alice"},
            authorization=("g1",),
            signature="",
        )
        delegation = clone_with_signature(
            delegation, crypto.sign_record(delegation, root_key.private_key_b64, root_key.key_id)
        )
        self.assertTrue(verifier.verify(delegation).valid)
        store.append(delegation)

        with_delegation = verifier.verify(work)
        auth_rule_2 = next(r for r in with_delegation.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule_2.status, RuleStatus.PASS)
        self.assertTrue(with_delegation.valid)

    def test_revocation_record_blocks_delegated_authorization(self) -> None:
        store = RecordStore()
        crypto = CryptoSuite()
        root_key = crypto.generate_key("root")
        alice_key = crypto.generate_key("alice")
        verifier = Verifier(store, crypto=crypto)

        genesis = Record(
            id="g1",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "boot", "value": 1},
            authorization=("g1",),
            signature="",
        )
        genesis = clone_with_signature(genesis, crypto.sign_record(genesis, root_key.private_key_b64, root_key.key_id))
        self.assertTrue(verifier.verify(genesis).valid)
        store.append(genesis)

        capability = Record(
            id="cap1",
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "authorize-work", "due_by": "2027-01-01"},
            authorization=("g1",),
            signature="",
        )
        capability = clone_with_signature(
            capability, crypto.sign_record(capability, root_key.private_key_b64, root_key.key_id)
        )
        self.assertTrue(verifier.verify(capability).valid)
        store.append(capability)

        delegation = Record(
            id="deleg1",
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate-authority", "due_by": "2027-01-01", "assignee": "alice"},
            authorization=("g1",),
            signature="",
        )
        delegation = clone_with_signature(
            delegation, crypto.sign_record(delegation, root_key.private_key_b64, root_key.key_id)
        )
        self.assertTrue(verifier.verify(delegation).valid)
        store.append(delegation)

        work = Record(
            id="work1",
            type=PrimitiveType.COMMITMENT,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "execute", "due_by": "2027-01-01"},
            authorization=("cap1",),
            signature="",
        )
        work = clone_with_signature(work, crypto.sign_record(work, alice_key.private_key_b64, alice_key.key_id))
        before_revoke = verifier.verify(work)
        self.assertTrue(before_revoke.valid)

        revocation = Record(
            id="rev1",
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "revoke-authority", "due_by": "2027-01-01", "assignee": "alice"},
            causes=("g1",),
            authorization=("deleg1",),
            signature="",
        )
        revocation = clone_with_signature(
            revocation, crypto.sign_record(revocation, root_key.private_key_b64, root_key.key_id)
        )
        self.assertTrue(verifier.verify(revocation).valid)
        store.append(revocation)

        after_revoke = verifier.verify(work)
        auth_rule = next(r for r in after_revoke.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule.status, RuleStatus.FAIL)
        self.assertIn("is revoked", auth_rule.reason)


if __name__ == "__main__":
    unittest.main()
