from __future__ import annotations

from dataclasses import dataclass
from math import exp, log

from .policy import AllocationDecision, AllocationPolicy, ConflictSet, WeightedPolicy


@dataclass(frozen=True)
class TrustSignal:
    claimant: str
    identity_confidence: float
    reputation_score: float
    age_days: float


class TrustModel:
    def __init__(self, *, half_life_days: float = 30.0) -> None:
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        self.half_life_days = half_life_days

    def decayed_weight(self, signal: TrustSignal) -> float:
        confidence = max(0.0, min(1.0, signal.identity_confidence))
        reputation = max(0.0, signal.reputation_score)
        decay = exp(-log(2.0) * max(0.0, signal.age_days) / self.half_life_days)
        return confidence * reputation * decay

    def derive_weights(self, signals: list[TrustSignal]) -> dict[str, float]:
        return {signal.claimant: self.decayed_weight(signal) for signal in signals}


class TrustWeightedPolicy:
    def __init__(self, trust_model: TrustModel, signals: list[TrustSignal]) -> None:
        self.trust_model = trust_model
        self.signals = signals

    def allocate(self, conflict_set: ConflictSet) -> AllocationDecision:
        weights = self.trust_model.derive_weights(self.signals)
        return WeightedPolicy(weights=weights).allocate(conflict_set)


def as_policy(policy: TrustWeightedPolicy) -> AllocationPolicy:
    return policy
