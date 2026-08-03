from __future__ import annotations

from dataclasses import dataclass

from .runtime_adapter import TerraNodeRuntimeAdapter


@dataclass(frozen=True)
class SubmissionRequest:
    identity: str
    claimant: str
    subject: str
    amount: float
    available: float


@dataclass(frozen=True)
class SubmissionOutcome:
    accepted: bool
    reason: str


class PublicSubmissionGateway:
    def __init__(self, *, max_requests_per_identity: int = 3, max_amount: float = 1_000_000.0) -> None:
        self.max_requests_per_identity = max_requests_per_identity
        self.max_amount = max_amount
        self._request_counts: dict[str, int] = {}

    def submit(self, adapter: TerraNodeRuntimeAdapter, request: SubmissionRequest) -> SubmissionOutcome:
        if not request.identity.strip():
            return SubmissionOutcome(accepted=False, reason="missing identity")
        if not request.subject.strip():
            return SubmissionOutcome(accepted=False, reason="missing subject")
        if request.amount <= 0.0 or request.amount > self.max_amount:
            return SubmissionOutcome(accepted=False, reason="invalid amount")
        if request.available <= 0.0:
            return SubmissionOutcome(accepted=False, reason="invalid available quantity")
        current = self._request_counts.get(request.identity, 0)
        if current >= self.max_requests_per_identity:
            return SubmissionOutcome(accepted=False, reason="rate limit exceeded")

        result = adapter.submit_intention(
            claimant=request.claimant,
            subject=request.subject,
            amount=request.amount,
            available=request.available,
        )
        self._request_counts[request.identity] = current + 1
        if result.verification.valid:
            return SubmissionOutcome(accepted=True, reason="accepted")
        return SubmissionOutcome(accepted=False, reason="rejected by verifier")
