from __future__ import annotations

from dataclasses import dataclass
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
