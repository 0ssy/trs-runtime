from __future__ import annotations

from dataclasses import dataclass
from runtime.record import PrimitiveType
from runtime.storage import RecordStore
from runtime.verifier import Verifier

from .runtime_adapter import TerraNodeRuntimeAdapter


@dataclass(frozen=True)
class IdentitySubmissionRequest:
    identity: str
    controller: str


@dataclass(frozen=True)
class IdentitySubmissionReceipt:
    identity: str
    accepted: bool
    reason: str
    record_id: str


@dataclass(frozen=True)
class IdentityRecordProof:
    record_id: str
    valid: bool
    causal_path: list[str]
    authorization_path: list[str]
    errors: list[str]


@dataclass(frozen=True)
class IdentityVerticalSliceResult:
    accepted_count: int
    rejected_count: int
    directory: dict[str, str]
    submission_receipts: list[IdentitySubmissionReceipt]
    replay_identities: dict[str, list[str]]
    proofs: list[IdentityRecordProof]


def run_identity_vertical_slice(
    requests: list[IdentitySubmissionRequest] | None = None,
) -> IdentityVerticalSliceResult:
    adapter = TerraNodeRuntimeAdapter(node_id="idapp")
    root = adapter.create_signed_self_authorized_root(
        author="identity-root",
        schema="trs.observation.v1",
        payload={"subject": "identity-registry", "value": {"registry": "global-v1"}},
        subject="identity-registry",
    )
    root_id = root.id
    root_verification = adapter.verifier.verify(root)
    if not root_verification.valid:
        raise ValueError(f"identity root rejected: {root_verification.errors}")
    adapter.store.append(root)

    capability = adapter.create_signed_record(
        type=PrimitiveType.COMMITMENT,
        author="identity-root",
        schema="trs.commitment.v1",
        payload={"action": "delegate-identity-attestation", "due_by": "2027-01-01"},
        causes=(root_id,),
        authorization=(root_id,),
        subject="identity-registry",
    )
    capability_id = capability.id
    cap_verification = adapter.verifier.verify(capability)
    if not cap_verification.valid:
        raise ValueError(f"identity capability rejected: {cap_verification.errors}")
    adapter.store.append(capability)

    active_requests = requests or [
        IdentitySubmissionRequest(identity="did:trs:alice", controller="alice"),
        IdentitySubmissionRequest(identity="did:trs:bob", controller="bob"),
        IdentitySubmissionRequest(identity="did:trs:alice", controller="mallory"),
        IdentitySubmissionRequest(identity="", controller="nobody"),
    ]

    receipts: list[IdentitySubmissionReceipt] = []
    directory: dict[str, str] = {}
    accepted = 0
    rejected = 0
    proofs: list[IdentityRecordProof] = []

    for request in active_requests:
        if not request.identity.strip():
            rejected += 1
            receipts.append(
                IdentitySubmissionReceipt(
                    identity=request.identity,
                    accepted=False,
                    reason="missing identity",
                    record_id="",
                )
            )
            continue
        if not request.controller.strip():
            rejected += 1
            receipts.append(
                IdentitySubmissionReceipt(
                    identity=request.identity,
                    accepted=False,
                    reason="missing controller",
                    record_id="",
                )
            )
            continue
        if request.identity in directory:
            rejected += 1
            receipts.append(
                IdentitySubmissionReceipt(
                    identity=request.identity,
                    accepted=False,
                    reason="duplicate identity",
                    record_id="",
                )
            )
            continue

        registration = adapter.create_signed_record(
            type=PrimitiveType.OBSERVATION,
            author=request.controller,
            schema="trs.observation.v1",
            payload={
                "subject": "identity-registration",
                "value": {"identity": request.identity, "controller": request.controller},
            },
            causes=(root_id,),
            subject="identity-registry",
        )
        registration_id = registration.id
        registration_verification = adapter.verifier.verify(registration)
        if not registration_verification.valid:
            rejected += 1
            receipts.append(
                IdentitySubmissionReceipt(
                    identity=request.identity,
                    accepted=False,
                    reason="rejected by verifier",
                    record_id=registration_id,
                )
            )
            continue
        adapter.store.append(registration)

        attestation = adapter.create_signed_record(
            type=PrimitiveType.COMMITMENT,
            author="identity-registrar",
            schema="trs.commitment.v1",
            payload={
                "action": "attest-identity",
                "due_by": "2027-01-01",
                "identity": request.identity,
                "controller": request.controller,
            },
            causes=(root_id, registration_id),
            authorization=(capability_id,),
            subject="identity-registry",
        )
        attestation_id = attestation.id
        attestation_verification = adapter.verifier.verify(attestation)
        if not attestation_verification.valid:
            rejected += 1
            receipts.append(
                IdentitySubmissionReceipt(
                    identity=request.identity,
                    accepted=False,
                    reason="attestation rejected by verifier",
                    record_id=attestation_id,
                )
            )
            continue
        adapter.store.append(attestation)

        proof_store = RecordStore()
        for existing in adapter.store.all():
            if existing.id == attestation.id:
                continue
            proof_store.append(existing)
        proof_verification = Verifier(proof_store, crypto=adapter.crypto).verify(attestation)
        proofs.append(
            IdentityRecordProof(
                record_id=attestation.id,
                valid=proof_verification.valid,
                causal_path=list(proof_verification.causal_path),
                authorization_path=list(proof_verification.authorization_path),
                errors=list(proof_verification.errors),
            )
        )

        directory[request.identity] = request.controller
        accepted += 1
        receipts.append(
            IdentitySubmissionReceipt(
                identity=request.identity,
                accepted=True,
                reason="accepted",
                record_id=registration_id,
            )
        )

    replay = adapter.replay()
    return IdentityVerticalSliceResult(
        accepted_count=accepted,
        rejected_count=rejected,
        directory=directory,
        submission_receipts=receipts,
        replay_identities=dict(replay.identities),
        proofs=proofs,
    )
