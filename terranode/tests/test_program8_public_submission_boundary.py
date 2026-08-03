from __future__ import annotations

import unittest

from terranode.terranode.boundary import PublicSubmissionGateway, SubmissionRequest
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


class Program8PublicBoundaryTests(unittest.TestCase):
    def test_gateway_blocks_malformed_and_rate_limits_untrusted_writers(self) -> None:
        gateway = PublicSubmissionGateway(max_requests_per_identity=2, max_amount=500.0)
        adapter = TerraNodeRuntimeAdapter(node_id="p8")

        malformed = gateway.submit(
            adapter,
            SubmissionRequest(identity="", claimant="alice", subject="warehouse-7", amount=80.0, available=100.0),
        )
        self.assertFalse(malformed.accepted)
        self.assertIn("identity", malformed.reason)

        first = gateway.submit(
            adapter,
            SubmissionRequest(identity="id-a", claimant="alice", subject="warehouse-7", amount=80.0, available=100.0),
        )
        second = gateway.submit(
            adapter,
            SubmissionRequest(identity="id-a", claimant="alice", subject="warehouse-7", amount=20.0, available=100.0),
        )
        third = gateway.submit(
            adapter,
            SubmissionRequest(identity="id-a", claimant="alice", subject="warehouse-7", amount=10.0, available=100.0),
        )
        self.assertTrue(first.accepted)
        self.assertTrue(second.accepted)
        self.assertFalse(third.accepted)
        self.assertIn("rate limit", third.reason)


if __name__ == "__main__":
    unittest.main()
