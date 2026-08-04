from __future__ import annotations

from dataclasses import dataclass

from ..policy import AllocationDecision, AllocationPolicy, ProRataPolicy
from ..runtime_adapter import TerraNodeRuntimeAdapter


@dataclass(frozen=True)
class ClaimSubmission:
    record_id: str
    accepted: bool
    errors: list[str]


class TerraNodePythonClient:
    def __init__(self, adapter: TerraNodeRuntimeAdapter | None = None) -> None:
        self.adapter = adapter or TerraNodeRuntimeAdapter(node_id="sdk-py")

    def submit_claim(self, *, claimant: str, subject: str, amount: float, available: float) -> ClaimSubmission:
        result = self.adapter.submit_intention(claimant=claimant, subject=subject, amount=amount, available=available)
        return ClaimSubmission(
            record_id=result.record_id,
            accepted=result.verification.valid,
            errors=list(result.verification.errors),
        )

    def resolve_subject(
        self, subject: str, policy: AllocationPolicy | None = None
    ) -> AllocationDecision:
        selected = policy or ProRataPolicy()
        decision = selected.allocate(self.adapter.find_conflicts(subject))
        self.adapter.apply_allocations(decision)
        return decision
