from __future__ import annotations

from dataclasses import dataclass

from runtime.record import Record

from ..policy import AllocationDecision, AllocationPolicy, ConflictSet
from ..runtime_adapter import TerraNodeRuntimeAdapter


@dataclass
class CoordinatorNode:
    node_id: str
    adapter: TerraNodeRuntimeAdapter

    @classmethod
    def create(cls, node_id: str) -> "CoordinatorNode":
        return cls(node_id=node_id, adapter=TerraNodeRuntimeAdapter(node_id=node_id))

    def seed_subject(self, *, subject: str, available: float, root_id: str, capability_id: str) -> None:
        self.adapter.seed_subject(
            subject=subject,
            available=available,
            root_id=root_id,
            capability_id=capability_id,
        )

    def submit_claim(self, claimant: str, subject: str, amount: float, available: float) -> None:
        result = self.adapter.submit_intention(claimant=claimant, subject=subject, amount=amount, available=available)
        if not result.verification.valid:
            raise ValueError(f"claim rejected: {result.verification.errors}")

    def find_conflicts(self, subject: str) -> ConflictSet:
        return self.adapter.find_conflicts(subject)

    def apply_policy(self, policy: AllocationPolicy, subject: str) -> AllocationDecision:
        decision = policy.allocate(self.adapter.find_conflicts(subject))
        self.adapter.apply_allocations(decision)
        return decision

    def export_records(self) -> list[Record]:
        return list(self.adapter.store.all())

    def receive_records(self, records: list[Record]) -> None:
        self.adapter.ingest_records(records)

    def inventory_ids(self) -> list[str]:
        return sorted(record.id for record in self.adapter.store.all())
