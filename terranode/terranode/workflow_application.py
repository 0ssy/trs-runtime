from __future__ import annotations

from dataclasses import dataclass

from runtime.record import PrimitiveType
from runtime.storage import RecordStore
from runtime.verifier import Verifier

from .boundary import PublicSubmissionGateway, SubmissionRequest
from .human import OfflineChannelClient
from .policy import ProRataPolicy
from .runtime_adapter import TerraNodeRuntimeAdapter


@dataclass(frozen=True)
class WorkflowRecordProof:
    record_id: str
    valid: bool
    causal_path: list[str]
    authorization_path: list[str]
    errors: list[str]


@dataclass(frozen=True)
class WorkflowVerticalSliceResult:
    accepted_count: int
    rejected_count: int
    allocations: dict[str, float]
    converged: bool
    unresolved_intentions: list[str]
    orphan_grant_commitments: list[str]
    proofs: list[WorkflowRecordProof]


def run_workflow_vertical_slice() -> WorkflowVerticalSliceResult:
    node_a = TerraNodeRuntimeAdapter(node_id="wf-a")
    node_b = TerraNodeRuntimeAdapter(node_id="wf-b")
    subject = "workflow-resource"
    available = 100.0

    node_a.seed_subject(subject=subject, available=available, root_id="wf-root", capability_id="wf-cap")
    node_b.seed_subject(subject=subject, available=available, root_id="wf-root", capability_id="wf-cap")

    gateway_a = PublicSubmissionGateway(max_requests_per_identity=5)
    gateway_b = PublicSubmissionGateway(max_requests_per_identity=5)
    sms_client = OfflineChannelClient(channel="sms")
    ussd_client = OfflineChannelClient(channel="ussd")

    sms_client.submit_offline(
        SubmissionRequest(identity="wf-id-a", claimant="alice", subject=subject, amount=80.0, available=available)
    )
    ussd_client.submit_offline(
        SubmissionRequest(identity="wf-id-b", claimant="bob", subject=subject, amount=60.0, available=available)
    )
    ussd_client.submit_offline(
        SubmissionRequest(identity="wf-id-c", claimant="carol", subject=subject, amount=-5.0, available=available)
    )

    sms_outcomes = sms_client.flush(gateway=gateway_a, adapter=node_a)
    ussd_outcomes = ussd_client.flush(gateway=gateway_b, adapter=node_b)

    node_a.sync_with_peer(node_b)
    node_b.sync_with_peer(node_a)

    accepted = sum(1 for outcome in [*sms_outcomes, *ussd_outcomes] if outcome.accepted)
    rejected = sum(1 for outcome in [*sms_outcomes, *ussd_outcomes] if not outcome.accepted)

    decision = ProRataPolicy().allocate(node_a.find_conflicts(subject))
    node_a.apply_allocations(decision)
    node_a.sync_with_peer(node_b)

    replay_a = node_a.replay()
    replay_b = node_b.replay()

    orphan_grant_commitments: list[str] = []
    for record_id in replay_a.coordination.orphan_commitments:
        record = node_a.store.get(record_id)
        if record is None:
            continue
        if record.payload.get("action") == "grant-allocation":
            orphan_grant_commitments.append(record_id)

    proofs: list[WorkflowRecordProof] = []
    for record in node_a.store.all():
        if record.subject != subject:
            continue
        if record.type != PrimitiveType.COMMITMENT:
            continue
        if record.payload.get("action") != "grant-allocation":
            continue
        proof_store = RecordStore()
        for existing in node_a.store.all():
            if existing.id == record.id:
                continue
            proof_store.append(existing)
        proof_verification = Verifier(proof_store, crypto=node_a.crypto).verify(record)
        proofs.append(
            WorkflowRecordProof(
                record_id=record.id,
                valid=proof_verification.valid,
                causal_path=list(proof_verification.causal_path),
                authorization_path=list(proof_verification.authorization_path),
                errors=list(proof_verification.errors),
            )
        )

    allocations = {allocation.claimant: allocation.granted for allocation in decision.allocations}
    converged = sorted(record.id for record in node_a.store.all()) == sorted(record.id for record in node_b.store.all())

    return WorkflowVerticalSliceResult(
        accepted_count=accepted,
        rejected_count=rejected,
        allocations=allocations,
        converged=converged and replay_a.coordination == replay_b.coordination,
        unresolved_intentions=list(replay_a.coordination.unresolved_intentions),
        orphan_grant_commitments=orphan_grant_commitments,
        proofs=proofs,
    )
