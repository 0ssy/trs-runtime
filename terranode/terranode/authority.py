from __future__ import annotations

from dataclasses import dataclass

from .policy import Allocation, AllocationDecision, AllocationPolicy, ConflictSet


@dataclass(frozen=True)
class AuthorityDecision:
    authority: str
    decision: AllocationDecision


class MultiAuthorityCoordinator:
    def __init__(self, influences: dict[str, float]) -> None:
        self.influences = influences

    def decide(
        self,
        *,
        conflict_set: ConflictSet,
        authority_policies: dict[str, AllocationPolicy],
    ) -> AuthorityDecision:
        weighted_grants: dict[str, float] = {}
        claimant_by_id: dict[str, str] = {}
        total_influence = 0.0
        for authority, policy in authority_policies.items():
            influence = max(0.0, self.influences.get(authority, 1.0))
            if influence == 0.0:
                continue
            total_influence += influence
            decision = policy.allocate(conflict_set)
            for allocation in decision.allocations:
                claimant_by_id[allocation.claim_id] = allocation.claimant
                weighted_grants[allocation.claim_id] = weighted_grants.get(allocation.claim_id, 0.0) + (
                    allocation.granted * influence
                )
        if total_influence <= 0.0:
            return AuthorityDecision(authority="none", decision=AllocationDecision(conflict_set.subject, []))
        allocations: list[Allocation] = []
        for claim in conflict_set.claims:
            averaged = weighted_grants.get(claim.claim_id, 0.0) / total_influence
            allocations.append(
                Allocation(claim_id=claim.claim_id, claimant=claimant_by_id.get(claim.claim_id, claim.claimant), granted=averaged)
            )
        return AuthorityDecision(
            authority="mediated",
            decision=AllocationDecision(subject=conflict_set.subject, allocations=allocations),
        )
