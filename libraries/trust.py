from __future__ import annotations

from runtime.graph import Graph


class TrustLibrary:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def nearest_common_ancestor(self, left_id: str, right_id: str) -> str | None:
        return self.graph.common_ancestor(left_id, right_id)
