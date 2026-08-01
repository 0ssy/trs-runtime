from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .graph import Graph
from .record import PrimitiveType
from .storage import StorageEngine


@dataclass(frozen=True)
class CoordinationView:
    intention_to_commitments: dict[str, list[str]]
    unresolved_intentions: list[str]
    orphan_commitments: list[str]


@dataclass(frozen=True)
class ReplaySnapshot:
    identities: dict[str, list[str]]
    workflows: dict[str, list[str]]
    contracts: list[str]
    reputation: dict[str, int]
    coordination: CoordinationView


class ReplayEngine:
    def __init__(self, store: StorageEngine) -> None:
        self.store = store
        self.graph = Graph(store)

    def replay(self) -> ReplaySnapshot:
        records = self.store.all()
        identities = self._replay_identities(records)
        workflows = self._replay_workflows(records)
        contracts = self._replay_contracts(records)
        reputation = self._replay_reputation(records)
        coordination = self._replay_coordination(records, contracts)
        return ReplaySnapshot(
            identities=identities,
            workflows=workflows,
            contracts=contracts,
            reputation=reputation,
            coordination=coordination,
        )

    def _replay_identities(self, records) -> dict[str, list[str]]:
        by_author: dict[str, list[str]] = defaultdict(list)
        for record in records:
            by_author[record.author].append(record.id)
        return dict(by_author)

    def _replay_workflows(self, records) -> dict[str, list[str]]:
        workflow: dict[str, list[str]] = {}
        for record in records:
            workflow[record.id] = sorted(self.graph.descendants(record.id))
        return workflow

    def _replay_contracts(self, records) -> list[str]:
        return [record.id for record in records if record.type == PrimitiveType.COMMITMENT]

    def _replay_reputation(self, records) -> dict[str, int]:
        return dict(Counter(record.author for record in records))

    def _replay_coordination(self, records, contracts: list[str]) -> CoordinationView:
        commitment_to_causes = {
            record.id: set(record.causes)
            for record in records
            if record.type == PrimitiveType.COMMITMENT
        }
        intention_ids = [record.id for record in records if record.type == PrimitiveType.INTENTION]
        intention_to_commitments: dict[str, list[str]] = {}
        unresolved_intentions: list[str] = []
        claimed_commitments: set[str] = set()

        for intention_id in intention_ids:
            linked = sorted(
                commitment_id
                for commitment_id, causes in commitment_to_causes.items()
                if intention_id in causes
            )
            intention_to_commitments[intention_id] = linked
            if not linked:
                unresolved_intentions.append(intention_id)
            claimed_commitments.update(linked)

        orphan_commitments = sorted(commitment_id for commitment_id in contracts if commitment_id not in claimed_commitments)
        return CoordinationView(
            intention_to_commitments=intention_to_commitments,
            unresolved_intentions=sorted(unresolved_intentions),
            orphan_commitments=orphan_commitments,
        )
