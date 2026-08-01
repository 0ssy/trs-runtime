from __future__ import annotations

from runtime.graph import Graph


class WorkflowLibrary:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def descendants(self, record_id: str) -> list[str]:
        return self.graph.descendants(record_id)
