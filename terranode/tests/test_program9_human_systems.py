from __future__ import annotations

import unittest

from terranode.terranode.boundary import PublicSubmissionGateway, SubmissionRequest
from terranode.terranode.human import OfflineChannelClient
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


class Program9HumanSystemsTests(unittest.TestCase):
    def test_offline_clients_flush_and_reconnect_preserve_history(self) -> None:
        node_a = TerraNodeRuntimeAdapter(node_id="p9a")
        node_b = TerraNodeRuntimeAdapter(node_id="p9b")
        node_a.seed_subject(
            subject="warehouse-7",
            available=100.0,
            root_id="warehouse-7-root",
            capability_id="warehouse-7-capability",
        )
        node_b.seed_subject(
            subject="warehouse-7",
            available=100.0,
            root_id="warehouse-7-root",
            capability_id="warehouse-7-capability",
        )

        gateway_a = PublicSubmissionGateway(max_requests_per_identity=5)
        gateway_b = PublicSubmissionGateway(max_requests_per_identity=5)
        sms_client = OfflineChannelClient(channel="sms")
        ussd_client = OfflineChannelClient(channel="ussd")

        sms_client.submit_offline(
            SubmissionRequest(identity="sms-1", claimant="alice", subject="warehouse-7", amount=80.0, available=100.0)
        )
        ussd_client.submit_offline(
            SubmissionRequest(identity="ussd-1", claimant="bob", subject="warehouse-7", amount=60.0, available=100.0)
        )

        sms_outcomes = sms_client.flush(gateway=gateway_a, adapter=node_a)
        ussd_outcomes = ussd_client.flush(gateway=gateway_b, adapter=node_b)
        self.assertTrue(all(outcome.accepted for outcome in sms_outcomes))
        self.assertTrue(all(outcome.accepted for outcome in ussd_outcomes))

        before_a = node_a.find_conflicts("warehouse-7")
        before_b = node_b.find_conflicts("warehouse-7")
        self.assertEqual(len(before_a.claims), 1)
        self.assertEqual(len(before_b.claims), 1)

        node_a.sync_with_peer(node_b)
        after_a = node_a.find_conflicts("warehouse-7")
        after_b = node_b.find_conflicts("warehouse-7")
        self.assertEqual(len(after_a.claims), 2)
        self.assertEqual(len(after_b.claims), 2)
        self.assertEqual(
            sorted(record.id for record in node_a.store.all()),
            sorted(record.id for record in node_b.store.all()),
        )


if __name__ == "__main__":
    unittest.main()
