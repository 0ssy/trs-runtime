from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record
from runtime.replay import ReplayEngine, ReplaySnapshot
from runtime.storage import RecordStore
from runtime.verifier import VerificationResult, Verifier

from .policy import AllocationDecision, Claim, ConflictSet


@dataclass(frozen=True)
class SubmittedIntention:
    record_id: str
    verification: VerificationResult


class TerraNodeRuntimeAdapter:
    def __init__(self) -> None:
        self.store = RecordStore()
        self.verifier = Verifier(self.store)
        self.query = QueryEngine(self.store)
        self.replay_engine = ReplayEngine(self.store)
        self._sequence = 0
        self._root_by_subject: dict[str, str] = {}
        self._capability_by_subject: dict[str, str] = {}

    def submit_intention(self, claimant: str, subject: str, amount: float, available: float) -> SubmittedIntention:
        self._ensure_subject_bootstrap(subject=subject, available=available)
        intention_id = self._next_id("intention")
        intention = Record(
            id=intention_id,
            type=PrimitiveType.INTENTION,
            author=claimant,
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "resource-allocation", "horizon": "program-1", "amount": float(amount)},
            causes=(self._root_by_subject[subject],),
            signature=f"sig:{intention_id}",
            subject=subject,
        )
        verification = self.verifier.verify(intention)
        if not verification.valid:
            return SubmittedIntention(record_id=intention_id, verification=verification)
        self.store.append(intention)
        return SubmittedIntention(record_id=intention_id, verification=verification)

    def find_conflicts(self, subject: str) -> ConflictSet:
        root_id = self._root_by_subject.get(subject)
        if root_id is None:
            return ConflictSet(subject=subject, available=0.0, claims=[])

        available = self._subject_available(root_id)
        closed_intentions = self._closed_intention_ids()
        claims: list[Claim] = []
        for record in self.store.children(root_id):
            if record.type != PrimitiveType.INTENTION:
                continue
            if record.subject != subject:
                continue
            if record.id in closed_intentions:
                continue
            claims.append(
                Claim(
                    claim_id=record.id,
                    claimant=record.author,
                    amount=float(record.payload.get("amount", 0.0)),
                )
            )
        return ConflictSet(subject=subject, available=available, claims=claims)

    def apply_allocations(self, decision: AllocationDecision) -> list[str]:
        root_id = self._root_by_subject[decision.subject]
        capability_id = self._capability_by_subject[decision.subject]
        appended: list[str] = []
        for allocation in decision.allocations:
            commitment_id = self._next_id("commitment")
            commitment = Record(
                id=commitment_id,
                type=PrimitiveType.COMMITMENT,
                author="allocator",
                timestamp=datetime.now(timezone.utc),
                schema="trs.commitment.v1",
                payload={
                    "action": "grant-allocation",
                    "due_by": "2027-01-01",
                    "claim_id": allocation.claim_id,
                    "claimant": allocation.claimant,
                    "granted": float(allocation.granted),
                },
                causes=(root_id, allocation.claim_id),
                authorization=(capability_id,),
                signature=f"sig:{commitment_id}",
                subject=decision.subject,
            )
            commitment_result = self.verifier.verify(commitment)
            if not commitment_result.valid:
                raise ValueError(f"commitment rejected: {commitment_result.errors}")
            self.store.append(commitment)
            appended.append(commitment_id)

            closure_id = self._next_id("closure")
            closure = Record(
                id=closure_id,
                type=PrimitiveType.OBSERVATION,
                author="allocator",
                timestamp=datetime.now(timezone.utc),
                schema="trs.observation.v1",
                payload={
                    "subject": "intention-closure",
                    "value": {"intention_id": allocation.claim_id, "status": "completed"},
                },
                causes=(allocation.claim_id, commitment_id),
                signature=f"sig:{closure_id}",
                subject=decision.subject,
            )
            closure_result = self.verifier.verify(closure)
            if not closure_result.valid:
                raise ValueError(f"closure rejected: {closure_result.errors}")
            self.store.append(closure)
            appended.append(closure_id)
        return appended

    def replay(self) -> ReplaySnapshot:
        return self.replay_engine.replay()

    def _ensure_subject_bootstrap(self, *, subject: str, available: float) -> None:
        if subject in self._root_by_subject:
            return
        root_id = self._next_id("root")
        root = Record(
            id=root_id,
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": subject, "value": {"available": float(available)}},
            signature=f"sig:{root_id}",
            subject=subject,
        )
        root_result = self.verifier.verify(root)
        if not root_result.valid:
            raise ValueError(f"root rejected: {root_result.errors}")
        self.store.append(root)
        self._root_by_subject[subject] = root_id

        capability_id = self._next_id("cap")
        capability = Record(
            id=capability_id,
            type=PrimitiveType.COMMITMENT,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "delegate-allocation", "due_by": "2027-01-01"},
            causes=(root_id,),
            authorization=(root_id,),
            signature=f"sig:{capability_id}",
            subject=subject,
        )
        cap_result = self.verifier.verify(capability)
        if not cap_result.valid:
            raise ValueError(f"capability rejected: {cap_result.errors}")
        self.store.append(capability)
        self._capability_by_subject[subject] = capability_id

    def _subject_available(self, root_id: str) -> float:
        root = self.store.get(root_id)
        if root is None:
            return 0.0
        value = root.payload.get("value")
        if isinstance(value, Mapping):
            raw = value.get("available", 0.0)
            try:
                return float(raw)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    def _closed_intention_ids(self) -> set[str]:
        closed: set[str] = set()
        for record in self.store.all():
            if record.type != PrimitiveType.OBSERVATION:
                continue
            if record.payload.get("subject") != "intention-closure":
                continue
            value = record.payload.get("value")
            if not isinstance(value, Mapping):
                continue
            intention_id = value.get("intention_id")
            status = value.get("status")
            if isinstance(intention_id, str) and status == "completed":
                closed.add(intention_id)
        return closed

    def _next_id(self, prefix: str) -> str:
        self._sequence += 1
        return f"{prefix}-{self._sequence:06d}"
