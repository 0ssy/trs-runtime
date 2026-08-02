from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Literal

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
    def __init__(
        self,
        store: StorageEngine,
        *,
        workflow_view: Literal["closure", "direct", "auto"] = "closure",
        sort_workflows: bool = True,
        sort_coordination: bool = True,
        auto_closure_limit: int = 5000,
    ) -> None:
        self.store = store
        self.workflow_view = workflow_view
        self.sort_workflows = sort_workflows
        self.sort_coordination = sort_coordination
        self.auto_closure_limit = auto_closure_limit
        child_ids_view = getattr(self.store, "child_ids_view", None)
        self._child_ids_view_provider = child_ids_view if callable(child_ids_view) else None
        child_ids = getattr(self.store, "child_ids", None)
        self._child_ids_provider = child_ids if callable(child_ids) else None
        child_ids_of_type = getattr(self.store, "child_ids_of_type", None)
        self._child_ids_of_type_provider = child_ids_of_type if callable(child_ids_of_type) else None
        children_of_type = getattr(self.store, "children_of_type", None)
        self._children_of_type_provider = children_of_type if callable(children_of_type) else None

    def replay(self, *, workflow_view: Literal["closure", "direct", "auto"] | None = None) -> ReplaySnapshot:
        records = self.store.all()
        identities = self._replay_identities(records)
        selected_view = workflow_view or self.workflow_view
        workflows = self._replay_workflows(records, selected_view)
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

    def _replay_workflows(
        self,
        records: Iterable,
        workflow_view: Literal["closure", "direct", "auto"],
    ) -> dict[str, list[str]]:
        materialized = list(records)
        if workflow_view == "auto":
            workflow_view = "closure" if len(materialized) <= self.auto_closure_limit else "direct"
        if workflow_view == "direct":
            return self._replay_workflows_direct(materialized)
        if workflow_view == "closure":
            return self._replay_workflows_closure(materialized)
        raise ValueError(f"unsupported workflow view: {workflow_view}")

    def _replay_workflows_direct(self, records: list) -> dict[str, list[str]]:
        if self._child_ids_view_provider is not None:
            workflow: dict[str, list[str]] = {}
            for record in records:
                children = self._child_ids_view_provider(record.id)
                workflow[record.id] = sorted(children) if self.sort_workflows else list(children)
            return workflow

        if self._child_ids_provider is not None:
            workflow: dict[str, list[str]] = {}
            for record in records:
                children = self._child_ids_provider(record.id)
                workflow[record.id] = sorted(children) if self.sort_workflows else list(children)
            return workflow

        children_by_parent: dict[str, list[str]] = defaultdict(list)
        workflow: dict[str, list[str]] = {record.id: [] for record in records}
        for record in records:
            for parent_id in record.causes:
                children_by_parent[parent_id].append(record.id)
        for record in records:
            children = children_by_parent.get(record.id, [])
            workflow[record.id] = sorted(children) if self.sort_workflows else list(children)
        return workflow

    def _replay_workflows_closure(self, records: list) -> dict[str, list[str]]:
        children_by_parent: dict[str, list[str]] = defaultdict(list)
        record_order: list[str] = []
        for record in records:
            record_order.append(record.id)
            for parent_id in record.causes:
                children_by_parent[parent_id].append(record.id)

        descendants_by_id: dict[str, set[str]] = {record_id: set() for record_id in record_order}
        for record_id in reversed(record_order):
            descendants = descendants_by_id[record_id]
            for child_id in children_by_parent.get(record_id, []):
                descendants.add(child_id)
                descendants.update(descendants_by_id.get(child_id, set()))

        workflow: dict[str, list[str]] = {}
        for record in records:
            values = descendants_by_id.get(record.id, set())
            workflow[record.id] = sorted(values) if self.sort_workflows else list(values)
        return workflow

    def _replay_contracts(self, records) -> list[str]:
        return [record.id for record in records if record.type == PrimitiveType.COMMITMENT]

    def _replay_reputation(self, records) -> dict[str, int]:
        return dict(Counter(record.author for record in records))

    def _replay_coordination(self, records, contracts: list[str]) -> CoordinationView:
        intention_ids = [record.id for record in records if record.type == PrimitiveType.INTENTION]
        intention_to_commitments: dict[str, list[str]] = {}
        unresolved_intentions: list[str] = []
        claimed_commitments_buffer: list[str] = []

        if self._child_ids_of_type_provider is not None:
            for intention_id in intention_ids:
                linked_base = self._child_ids_of_type_provider(intention_id, PrimitiveType.COMMITMENT)
                linked = sorted(linked_base) if self.sort_coordination else list(linked_base)
                intention_to_commitments[intention_id] = linked
                if not linked:
                    unresolved_intentions.append(intention_id)
                else:
                    claimed_commitments_buffer.extend(linked)
        elif self._children_of_type_provider is not None:
            for intention_id in intention_ids:
                linked_base = [record.id for record in self._children_of_type_provider(intention_id, PrimitiveType.COMMITMENT)]
                linked = sorted(linked_base) if self.sort_coordination else linked_base
                intention_to_commitments[intention_id] = linked
                if not linked:
                    unresolved_intentions.append(intention_id)
                else:
                    claimed_commitments_buffer.extend(linked)
        else:
            intention_set = set(intention_ids)
            commitments_by_intention: dict[str, list[str]] = defaultdict(list)
            for record in records:
                if record.type != PrimitiveType.COMMITMENT:
                    continue
                for cause_id in record.causes:
                    if cause_id in intention_set:
                        commitments_by_intention[cause_id].append(record.id)
            for intention_id in intention_ids:
                linked_base = commitments_by_intention.get(intention_id, [])
                linked = sorted(linked_base) if self.sort_coordination else list(linked_base)
                intention_to_commitments[intention_id] = linked
                if not linked:
                    unresolved_intentions.append(intention_id)
                else:
                    claimed_commitments_buffer.extend(linked)

        claimed_commitments = set(claimed_commitments_buffer)
        orphan_base = [commitment_id for commitment_id in contracts if commitment_id not in claimed_commitments]
        orphan_commitments = sorted(orphan_base) if self.sort_coordination else orphan_base
        return CoordinationView(
            intention_to_commitments=intention_to_commitments,
            unresolved_intentions=sorted(unresolved_intentions) if self.sort_coordination else unresolved_intentions,
            orphan_commitments=orphan_commitments,
        )
