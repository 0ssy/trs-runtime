from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import Verifier

from .runtime_adapter import TerraNodeRuntimeAdapter
from .trust import TrustModel, TrustSignal, TrustWeightedPolicy


@dataclass(frozen=True)
class ReputationSignalRequest:
    claimant: str
    identity_confidence: float
    reputation_score: float
    age_days: float


@dataclass(frozen=True)
class ReputationSignalReceipt:
    claimant: str
    accepted: bool
    reason: str
    record_id: str


@dataclass(frozen=True)
class ReputationRecordProof:
    record_id: str
    valid: bool
    causal_path: list[str]
    authorization_path: list[str]
    errors: list[str]


@dataclass(frozen=True)
class ReputationVerticalSliceResult:
    accepted_count: int
    rejected_count: int
    allocations: dict[str, float]
    weights: dict[str, float]
    replay_reputation: dict[str, int]
    unresolved_intentions: list[str]
    orphan_grant_commitments: list[str]
    signal_receipts: list[ReputationSignalReceipt]
    proofs: list[ReputationRecordProof]


def run_reputation_vertical_slice(
    requests: list[ReputationSignalRequest] | None = None,
) -> ReputationVerticalSliceResult:
    adapter = TerraNodeRuntimeAdapter(node_id="repapp")
    sequence = 0

    def next_id(prefix: str) -> str:
        nonlocal sequence
        sequence += 1
        return f"rep-ledger-{prefix}-{sequence:06d}"

    root_id = next_id("root")
    root = Record(
        id=root_id,
        type=PrimitiveType.OBSERVATION,
        author="reputation-root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "reputation-ledger", "value": {"epoch": "v1"}},
        authorization=(root_id,),
        signature=f"sig:{root_id}",
        subject="reputation-ledger",
    )
    root_verification = adapter.verifier.verify(root)
    if not root_verification.valid:
        raise ValueError(f"reputation root rejected: {root_verification.errors}")
    adapter.store.append(root)

    active_requests = requests or [
        ReputationSignalRequest(claimant="alice", identity_confidence=0.95, reputation_score=0.9, age_days=2.0),
        ReputationSignalRequest(claimant="bob", identity_confidence=0.8, reputation_score=0.5, age_days=10.0),
        ReputationSignalRequest(claimant="", identity_confidence=0.7, reputation_score=0.6, age_days=1.0),
        ReputationSignalRequest(claimant="eve", identity_confidence=1.2, reputation_score=-0.2, age_days=0.0),
    ]

    accepted = 0
    rejected = 0
    receipts: list[ReputationSignalReceipt] = []
    signals: list[TrustSignal] = []

    for request in active_requests:
        if not request.claimant.strip():
            rejected += 1
            receipts.append(
                ReputationSignalReceipt(
                    claimant=request.claimant,
                    accepted=False,
                    reason="missing claimant",
                    record_id="",
                )
            )
            continue
        if not (0.0 <= request.identity_confidence <= 1.0):
            rejected += 1
            receipts.append(
                ReputationSignalReceipt(
                    claimant=request.claimant,
                    accepted=False,
                    reason="identity confidence out of range",
                    record_id="",
                )
            )
            continue
        if request.reputation_score < 0.0:
            rejected += 1
            receipts.append(
                ReputationSignalReceipt(
                    claimant=request.claimant,
                    accepted=False,
                    reason="negative reputation score",
                    record_id="",
                )
            )
            continue

        signal_id = next_id("signal")
        signal_record = Record(
            id=signal_id,
            type=PrimitiveType.OBSERVATION,
            author=request.claimant,
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={
                "subject": "reputation-signal",
                "value": {
                    "claimant": request.claimant,
                    "identity_confidence": request.identity_confidence,
                    "reputation_score": request.reputation_score,
                    "age_days": request.age_days,
                },
            },
            causes=(root_id,),
            signature=f"sig:{signal_id}",
            subject="reputation-ledger",
        )
        verification = adapter.verifier.verify(signal_record)
        if not verification.valid:
            rejected += 1
            receipts.append(
                ReputationSignalReceipt(
                    claimant=request.claimant,
                    accepted=False,
                    reason="rejected by verifier",
                    record_id=signal_id,
                )
            )
            continue

        adapter.store.append(signal_record)
        signals.append(
            TrustSignal(
                claimant=request.claimant,
                identity_confidence=request.identity_confidence,
                reputation_score=request.reputation_score,
                age_days=request.age_days,
            )
        )
        accepted += 1
        receipts.append(
            ReputationSignalReceipt(
                claimant=request.claimant,
                accepted=True,
                reason="accepted",
                record_id=signal_id,
            )
        )

    funding_subject = "reputation-fund"
    available = 100.0
    for signal in signals:
        submission = adapter.submit_intention(
            claimant=signal.claimant,
            subject=funding_subject,
            amount=100.0,
            available=available,
        )
        if not submission.verification.valid:
            raise ValueError(f"reputation intention rejected: {submission.verification.errors}")

    trust_model = TrustModel(half_life_days=30.0)
    policy = TrustWeightedPolicy(trust_model=trust_model, signals=signals)
    conflict_set = adapter.find_conflicts(funding_subject)
    decision = policy.allocate(conflict_set)
    adapter.apply_allocations(decision)
    replay = adapter.replay()

    weights = trust_model.derive_weights(signals)
    allocations = {allocation.claimant: allocation.granted for allocation in decision.allocations}

    orphan_grant_commitments: list[str] = []
    for record_id in replay.coordination.orphan_commitments:
        record = adapter.store.get(record_id)
        if record is None:
            continue
        if record.payload.get("action") == "grant-allocation":
            orphan_grant_commitments.append(record_id)

    proofs: list[ReputationRecordProof] = []
    for record in adapter.store.all():
        if record.subject != funding_subject:
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
        proof_verification = Verifier(
            proof_store, allow_insecure_signatures=True, enforce_canonical_record_id=False
        ).verify(record)
        proofs.append(
            ReputationRecordProof(
                record_id=record.id,
                valid=proof_verification.valid,
                causal_path=list(proof_verification.causal_path),
                authorization_path=list(proof_verification.authorization_path),
                errors=list(proof_verification.errors),
            )
        )

    return ReputationVerticalSliceResult(
        accepted_count=accepted,
        rejected_count=rejected,
        allocations=allocations,
        weights=weights,
        replay_reputation=dict(replay.reputation),
        unresolved_intentions=list(replay.coordination.unresolved_intentions),
        orphan_grant_commitments=orphan_grant_commitments,
        signal_receipts=receipts,
        proofs=proofs,
    )
