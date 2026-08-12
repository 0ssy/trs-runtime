from __future__ import annotations

from dataclasses import dataclass

from runtime.record import PrimitiveType
from runtime.storage import RecordStore
from runtime.verifier import Verifier

from .boundary import PublicSubmissionGateway, SubmissionRequest
from .policy import AllocationPolicy, ProRataPolicy
from .runtime_adapter import TerraNodeRuntimeAdapter
from .sdk import TerraNodePythonClient


@dataclass(frozen=True)
class ApplicationBacklog:
    flagship: tuple[str, ...]
    domain_services: tuple[str, ...]
    infrastructure_deferred: tuple[str, ...]


@dataclass(frozen=True)
class SubmissionReceipt:
    identity: str
    accepted: bool
    reason: str


@dataclass(frozen=True)
class RecordProof:
    record_id: str
    valid: bool
    causal_path: list[str]
    authorization_path: list[str]
    errors: list[str]


@dataclass(frozen=True)
class VerticalSliceResult:
    subject: str
    accepted_count: int
    rejected_count: int
    conflict_claim_count: int
    allocations: dict[str, float]
    unresolved_intentions: list[str]
    orphan_commitments: list[str]
    orphan_grant_commitments: list[str]
    submission_receipts: list[SubmissionReceipt]
    proofs: list[RecordProof]


def app_validation_backlog() -> ApplicationBacklog:
    return ApplicationBacklog(
        flagship=("terranode",),
        domain_services=("identity-service", "reputation-service", "workflow-engine"),
        infrastructure_deferred=(
            "openapi-generation-expansion",
            "hosted-node",
            "kubernetes",
            "registry",
            "templates",
            "vscode-extension",
        ),
    )


def run_vertical_slice(
    *,
    subject: str = "warehouse-7",
    available: float = 100.0,
    requests: list[SubmissionRequest] | None = None,
    policy: AllocationPolicy | None = None,
    max_requests_per_identity: int = 1,
) -> VerticalSliceResult:
    adapter = TerraNodeRuntimeAdapter(node_id="app1")
    client = TerraNodePythonClient(adapter=adapter)
    gateway = PublicSubmissionGateway(max_requests_per_identity=max_requests_per_identity)
    selected_policy = policy or ProRataPolicy()
    default_requests = [
        SubmissionRequest(identity="id-a", claimant="alice", subject=subject, amount=80.0, available=available),
        SubmissionRequest(identity="id-b", claimant="bob", subject=subject, amount=60.0, available=available),
        SubmissionRequest(identity="id-a", claimant="alice", subject=subject, amount=10.0, available=available),
    ]
    active_requests = requests or default_requests

    receipts: list[SubmissionReceipt] = []
    accepted = 0
    rejected = 0
    for request in active_requests:
        outcome = gateway.submit(adapter, request)
        receipts.append(
            SubmissionReceipt(
                identity=request.identity,
                accepted=outcome.accepted,
                reason=outcome.reason,
            )
        )
        if outcome.accepted:
            accepted += 1
        else:
            rejected += 1

    conflict_set = adapter.find_conflicts(subject)
    if conflict_set.claims:
        decision = client.resolve_subject(subject, selected_policy)
    else:
        decision = selected_policy.allocate(conflict_set)

    replay = adapter.replay()
    allocations = {allocation.claimant: allocation.granted for allocation in decision.allocations}
    orphan_grant_commitments: list[str] = []
    for record_id in replay.coordination.orphan_commitments:
        record = adapter.store.get(record_id)
        if record is None:
            continue
        if record.payload.get("action") == "grant-allocation":
            orphan_grant_commitments.append(record_id)

    proofs: list[RecordProof] = []
    for record in adapter.store.all():
        if record.subject != subject:
            continue
        if record.type != PrimitiveType.COMMITMENT:
            continue
        if record.payload.get("action") != "grant-allocation":
            continue
        proof_store = RecordStore()
        for existing in adapter.store.all():
            if existing.id == record.id:
                continue
            proof_store.append(existing)
        verification = Verifier(
            proof_store, allow_insecure_signatures=True, enforce_canonical_record_id=False
        ).verify(record)
        proofs.append(
            RecordProof(
                record_id=record.id,
                valid=verification.valid,
                causal_path=list(verification.causal_path),
                authorization_path=list(verification.authorization_path),
                errors=list(verification.errors),
            )
        )

    return VerticalSliceResult(
        subject=subject,
        accepted_count=accepted,
        rejected_count=rejected,
        conflict_claim_count=len(conflict_set.claims),
        allocations=allocations,
        unresolved_intentions=list(replay.coordination.unresolved_intentions),
        orphan_commitments=list(replay.coordination.orphan_commitments),
        orphan_grant_commitments=orphan_grant_commitments,
        submission_receipts=receipts,
        proofs=proofs,
    )
