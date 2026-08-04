from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Protocol


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claimant: str
    amount: float


@dataclass(frozen=True)
class ConflictSet:
    subject: str
    available: float
    claims: list[Claim]


@dataclass(frozen=True)
class Allocation:
    claim_id: str
    claimant: str
    granted: float


@dataclass(frozen=True)
class AllocationDecision:
    subject: str
    allocations: list[Allocation]


class AllocationPolicy(Protocol):
    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision: ...


class ProRataPolicy:
    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        total_claimed = sum(max(0.0, claim.amount) for claim in conflict_set.claims)
        if total_claimed <= 0.0 or conflict_set.available <= 0.0:
            return AllocationDecision(
                subject=conflict_set.subject,
                allocations=[
                    Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=0.0)
                    for claim in conflict_set.claims
                ],
            )
        scale = conflict_set.available / total_claimed
        allocations = [
            Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=claim.amount * scale)
            for claim in conflict_set.claims
        ]
        return AllocationDecision(subject=conflict_set.subject, allocations=allocations)


class PriorityPolicy:
    def __init__(self, priorities: dict[str, int] | None = None) -> None:
        self.priorities = priorities or {}

    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        allocations = [Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=0.0) for claim in conflict_set.claims]
        if conflict_set.available <= 0:
            return AllocationDecision(subject=conflict_set.subject, allocations=allocations)
        remaining = float(conflict_set.available)
        indexed = sorted(
            enumerate(conflict_set.claims),
            key=lambda pair: (-self.priorities.get(pair[1].claimant, 0), pair[0]),
        )
        grants: dict[str, float] = {}
        for _, claim in indexed:
            grant = min(max(0.0, claim.amount), remaining)
            grants[claim.claim_id] = grant
            remaining -= grant
            if remaining <= 0:
                break
        return AllocationDecision(
            subject=conflict_set.subject,
            allocations=[
                Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=grants.get(claim.claim_id, 0.0))
                for claim in conflict_set.claims
            ],
        )


class WeightedPolicy:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or {}

    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        weighted_total = 0.0
        weighted_claims: list[tuple[Claim, float]] = []
        for claim in conflict_set.claims:
            weight = max(0.0, self.weights.get(claim.claimant, 1.0))
            weighted = max(0.0, claim.amount) * weight
            weighted_claims.append((claim, weighted))
            weighted_total += weighted
        if weighted_total <= 0.0 or conflict_set.available <= 0.0:
            return AllocationDecision(
                subject=conflict_set.subject,
                allocations=[
                    Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=0.0)
                    for claim in conflict_set.claims
                ],
            )
        scale = conflict_set.available / weighted_total
        return AllocationDecision(
            subject=conflict_set.subject,
            allocations=[
                Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=weighted * scale)
                for claim, weighted in weighted_claims
            ],
        )


class AuctionPolicy:
    def __init__(self, bids: dict[str, float] | None = None) -> None:
        self.bids = bids or {}

    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        if not conflict_set.claims or conflict_set.available <= 0.0:
            return AllocationDecision(subject=conflict_set.subject, allocations=[])
        winner = max(
            conflict_set.claims,
            key=lambda claim: (self.bids.get(claim.claimant, claim.amount), claim.amount),
        )
        allocations = []
        for claim in conflict_set.claims:
            grant = min(max(0.0, winner.amount), conflict_set.available) if claim.claim_id == winner.claim_id else 0.0
            allocations.append(Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=grant))
        return AllocationDecision(subject=conflict_set.subject, allocations=allocations)


class EmergencyOverridePolicy:
    def __init__(self, emergency_claimant: str) -> None:
        self.emergency_claimant = emergency_claimant

    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        if conflict_set.available <= 0:
            return AllocationDecision(
                subject=conflict_set.subject,
                allocations=[
                    Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=0.0)
                    for claim in conflict_set.claims
                ],
            )
        emergency_claim = next((claim for claim in conflict_set.claims if claim.claimant == self.emergency_claimant), None)
        if emergency_claim is None:
            return ProRataPolicy().allocate(conflict_set)
        remaining = float(conflict_set.available)
        emergency_grant = min(max(0.0, emergency_claim.amount), remaining)
        remaining -= emergency_grant
        others = [claim for claim in conflict_set.claims if claim.claim_id != emergency_claim.claim_id]
        base = ProRataPolicy().allocate(
            ConflictSet(subject=conflict_set.subject, available=remaining, claims=others)
        )
        by_id = {allocation.claim_id: allocation.granted for allocation in base.allocations}
        by_id[emergency_claim.claim_id] = emergency_grant
        return AllocationDecision(
            subject=conflict_set.subject,
            allocations=[
                Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=by_id.get(claim.claim_id, 0.0))
                for claim in conflict_set.claims
            ],
        )


class LotteryPolicy:
    def __init__(self, *, seed: str = "terranode-lottery") -> None:
        self.seed = seed

    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        if not conflict_set.claims or conflict_set.available <= 0.0:
            return AllocationDecision(
                subject=conflict_set.subject,
                allocations=[
                    Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=0.0)
                    for claim in conflict_set.claims
                ],
            )
        winner = max(
            conflict_set.claims,
            key=lambda claim: hashlib.sha256(f"{self.seed}:{claim.claim_id}".encode("utf-8")).hexdigest(),
        )
        granted = min(max(0.0, winner.amount), conflict_set.available)
        return AllocationDecision(
            subject=conflict_set.subject,
            allocations=[
                Allocation(
                    claim_id=claim.claim_id,
                    claimant=claim.claimant,
                    granted=granted if claim.claim_id == winner.claim_id else 0.0,
                )
                for claim in conflict_set.claims
            ],
        )


class FairSharePolicy:
    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        claims = list(conflict_set.claims)
        if not claims or conflict_set.available <= 0.0:
            return AllocationDecision(
                subject=conflict_set.subject,
                allocations=[
                    Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=0.0)
                    for claim in claims
                ],
            )

        remaining = float(conflict_set.available)
        unmet = {claim.claim_id: max(0.0, claim.amount) for claim in claims}
        grants = {claim.claim_id: 0.0 for claim in claims}

        while remaining > 0.0 and unmet:
            share = remaining / len(unmet)
            consumed = 0.0
            finished: list[str] = []
            for claim_id, needed in unmet.items():
                grant = min(needed, share)
                grants[claim_id] += grant
                consumed += grant
                unmet[claim_id] = needed - grant
                if unmet[claim_id] <= 1e-9:
                    finished.append(claim_id)
            remaining -= consumed
            for claim_id in finished:
                unmet.pop(claim_id, None)
            if consumed <= 1e-12:
                break

        return AllocationDecision(
            subject=conflict_set.subject,
            allocations=[
                Allocation(claim_id=claim.claim_id, claimant=claim.claimant, granted=grants.get(claim.claim_id, 0.0))
                for claim in claims
            ],
        )
