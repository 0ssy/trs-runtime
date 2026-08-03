from __future__ import annotations

from datetime import datetime, timezone
import unittest

from runtime.record import PrimitiveType, Record
from terranode.terranode.capability import CapabilityRegistry, CapabilityToken
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


class Program7CapabilitySecurityTests(unittest.TestCase):
    def test_forged_authority_and_non_transitive_and_expiry_blocked(self) -> None:
        adapter = TerraNodeRuntimeAdapter(node_id="p7")
        seed = adapter.submit_intention("alice", "warehouse-7", 80.0, 100.0)
        self.assertTrue(seed.verification.valid)

        intention_id = seed.record_id
        root_id = next(iter(adapter._root_by_subject.values()))
        forged = Record(
            id="forged-commitment",
            type=PrimitiveType.COMMITMENT,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "grant-allocation", "due_by": "2027-01-01"},
            causes=(root_id, intention_id),
            authorization=("ghost-capability",),
            signature="sig:forged",
            subject="warehouse-7",
        )
        result = adapter.verifier.verify(forged)
        self.assertFalse(result.valid)
        self.assertTrue(any("missing authorization records" in error for error in result.errors))

        registry = CapabilityRegistry()
        root = CapabilityToken(
            token_id="cap-root",
            subject="warehouse-7",
            grantee="allocator",
            expires_at_epoch=2_000_000_000,
            issuer_token_id=None,
        )
        delegated = CapabilityToken(
            token_id="cap-delegated",
            subject="warehouse-7",
            grantee="delegate",
            expires_at_epoch=2_000_000_000,
            issuer_token_id="cap-root",
        )
        registry.issue(root)
        registry.issue(delegated)
        ok_root, _ = registry.validate(
            token_id="cap-root", subject="warehouse-7", actor="allocator", now_epoch=1_800_000_000
        )
        self.assertTrue(ok_root)
        ok_delegated, reason_delegated = registry.validate(
            token_id="cap-delegated", subject="warehouse-7", actor="delegate", now_epoch=1_800_000_000
        )
        self.assertFalse(ok_delegated)
        self.assertIn("non-transitive", reason_delegated)

        expired = CapabilityToken(
            token_id="cap-expired",
            subject="warehouse-7",
            grantee="allocator",
            expires_at_epoch=1000,
            issuer_token_id=None,
        )
        registry.issue(expired)
        ok_expired, reason_expired = registry.validate(
            token_id="cap-expired", subject="warehouse-7", actor="allocator", now_epoch=2000
        )
        self.assertFalse(ok_expired)
        self.assertIn("expired", reason_expired)


if __name__ == "__main__":
    unittest.main()
