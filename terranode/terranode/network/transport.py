from __future__ import annotations

from dataclasses import dataclass

from .node import CoordinatorNode


@dataclass(frozen=True)
class PendingDelivery:
    source: str
    target: str
    record_ids: list[str]


class InMemoryTransport:
    def __init__(self) -> None:
        self._nodes: dict[str, CoordinatorNode] = {}
        self._blocked_links: set[frozenset[str]] = set()
        self._queue: list[tuple[str, str, list]] = []

    def register(self, node: CoordinatorNode) -> None:
        self._nodes[node.node_id] = node

    def partition(self, left: str, right: str) -> None:
        self._blocked_links.add(frozenset((left, right)))

    def heal(self, left: str, right: str) -> None:
        self._blocked_links.discard(frozenset((left, right)))

    def heal_all(self) -> None:
        self._blocked_links.clear()

    def enqueue_sync(self, source: str, target: str, *, duplicate: bool = False, out_of_order: bool = False) -> None:
        source_node = self._nodes[source]
        records = source_node.export_records()
        if out_of_order:
            records = list(reversed(records))
        self._queue.append((source, target, records))
        if duplicate:
            self._queue.append((source, target, list(records)))

    def flush(self) -> list[PendingDelivery]:
        delivered: list[PendingDelivery] = []
        pending = list(self._queue)
        self._queue.clear()
        for source, target, records in pending:
            if frozenset((source, target)) in self._blocked_links:
                self._queue.append((source, target, records))
                continue
            source_node = self._nodes[source]
            target_node = self._nodes[target]
            target_node.adapter.crypto.import_public_keys(source_node.adapter.crypto.export_public_keys())
            target_node.receive_records(records)
            delivered.append(
                PendingDelivery(source=source, target=target, record_ids=[record.id for record in records])
            )
        return delivered
