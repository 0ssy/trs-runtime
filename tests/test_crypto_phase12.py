from __future__ import annotations

from datetime import datetime, timezone
import unittest

from runtime.crypto import CryptoSuite, clone_with_signature
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import RuleStatus, Verifier


class CryptoPhase12Tests(unittest.TestCase):
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

    def test_delegation_required_for_authorization_chain_when_crypto_enabled(self) -> None:
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
            payload={"action": "delegate", "due_by": "2027-01-01"},
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

        crypto.grant_delegation("root", "alice")
        with_delegation = verifier.verify(work)
        auth_rule_2 = next(r for r in with_delegation.rules if r.rule_id == "6.1")
        self.assertEqual(auth_rule_2.status, RuleStatus.PASS)
        self.assertTrue(with_delegation.valid)


if __name__ == "__main__":
    unittest.main()
