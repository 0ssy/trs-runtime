from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from typing import Iterable

from .network_sync import sync_nodes
from .record import PrimitiveType, Record
from .storage import RecordStore
from .verifier import Verifier


@dataclass
class SimNode:
    name: str
    store: RecordStore
    verifier: Verifier


@dataclass(frozen=True)
class RoundResult:
    round_index: int
    links: list[tuple[str, str]]
    rejected_by_target: dict[str, list[str]]


@dataclass(frozen=True)
class MultiNodeSimulationResult:
    converged: bool
    rounds: list[RoundResult]
    inventories: dict[str, list[str]]


def make_node(name: str, seed: Iterable[Record] = ()) -> SimNode:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    for record in seed:
        if not store.exists(record.id):
            store.append(record)
    return SimNode(name=name, store=store, verifier=verifier)


def simulate_partitioned_sync(
    nodes: list[SimNode], round_links: list[list[tuple[str, str]]]
) -> MultiNodeSimulationResult:
    by_name = {node.name: node for node in nodes}
    history: list[RoundResult] = []

    for round_index, links in enumerate(round_links, start=1):
        rejected_by_target: dict[str, list[str]] = {}
        for left_name, right_name in links:
            left = by_name[left_name]
            right = by_name[right_name]

            left_to_right = sync_nodes(left.store, right.store, right.verifier)
            right_to_left = sync_nodes(right.store, left.store, left.verifier)

            if left_to_right.rejected_ids:
                rejected_by_target.setdefault(right.name, []).extend(left_to_right.rejected_ids)
            if right_to_left.rejected_ids:
                rejected_by_target.setdefault(left.name, []).extend(right_to_left.rejected_ids)

        history.append(
            RoundResult(round_index=round_index, links=links, rejected_by_target=rejected_by_target)
        )

    inventories = {node.name: sorted(record.id for record in node.store.all()) for node in nodes}
    converged = _all_equal(list(inventories.values()))
    return MultiNodeSimulationResult(converged=converged, rounds=history, inventories=inventories)


def fully_connected_links(node_names: list[str]) -> list[tuple[str, str]]:
    return [(a, b) for a, b in combinations(node_names, 2)]


def make_linear_records(length: int) -> list[Record]:
    if length < 1:
        return []
    records: list[Record] = []
    genesis = Record(
        id="g0",
        type=PrimitiveType.OBSERVATION,
        author="root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "boot", "value": 1},
        authorization=("g0",),
        signature="sig:g0",
    )
    records.append(genesis)
    prev = genesis.id
    for i in range(1, length):
        primitive = [PrimitiveType.INTENTION, PrimitiveType.COMMITMENT, PrimitiveType.OBSERVATION][i % 3]
        if primitive == PrimitiveType.INTENTION:
            schema = "trs.intention.v1"
            payload = {"goal": f"goal-{i}", "horizon": "Q1"}
            authorization: tuple[str, ...] = ()
        elif primitive == PrimitiveType.COMMITMENT:
            schema = "trs.commitment.v1"
            payload = {"action": f"action-{i}", "due_by": "2027-01-01"}
            authorization = ("g0",)
        else:
            schema = "trs.observation.v1"
            payload = {"subject": f"s-{i}", "value": i}
            authorization = ()

        record = Record(
            id=f"r{i}",
            type=primitive,
            author=f"user{i % 4}",
            timestamp=datetime.now(timezone.utc),
            schema=schema,
            payload=payload,
            causes=(prev,),
            authorization=authorization,
            signature=f"sig:r{i}",
        )
        records.append(record)
        prev = record.id
    return records


def _all_equal(values: list[list[str]]) -> bool:
    if not values:
        return True
    first = values[0]
    return all(value == first for value in values[1:])
