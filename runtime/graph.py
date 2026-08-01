from __future__ import annotations

from collections import defaultdict, deque

from .storage import StorageEngine


class Graph:
    def __init__(self, store: StorageEngine) -> None:
        self.store = store

    def parents(self, record_id: str) -> list[str]:
        return self.store.parents(record_id)

    def children(self, record_id: str) -> list[str]:
        return [r.id for r in self.store.children(record_id)]

    def ancestors(self, record_id: str) -> list[str]:
        visited: set[str] = set()
        stack = list(self.parents(record_id))
        while stack:
            parent = stack.pop()
            if parent in visited:
                continue
            visited.add(parent)
            stack.extend(self.parents(parent))
        return list(visited)

    def descendants(self, record_id: str) -> list[str]:
        visited: set[str] = set()
        stack = self.children(record_id)
        while stack:
            child = stack.pop()
            if child in visited:
                continue
            visited.add(child)
            stack.extend(self.children(child))
        return list(visited)

    def topological_order(self) -> list[str]:
        records = self.store.all()
        indegree: dict[str, int] = {r.id: 0 for r in records}
        adjacency: dict[str, list[str]] = defaultdict(list)
        for record in records:
            for parent in record.causes:
                if parent in indegree:
                    indegree[record.id] += 1
                    adjacency[parent].append(record.id)

        queue = deque([rid for rid, degree in indegree.items() if degree == 0])
        order: list[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for child in adjacency[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        return order

    def common_ancestor(self, left_id: str, right_id: str) -> str | None:
        left_anc = set(self.ancestors(left_id)) | {left_id}
        queue = deque([right_id])
        visited = {right_id}
        while queue:
            current = queue.popleft()
            if current in left_anc:
                return current
            for parent in self.parents(current):
                if parent not in visited:
                    visited.add(parent)
                    queue.append(parent)
        return None
