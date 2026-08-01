from __future__ import annotations

from runtime.query import QueryEngine
from runtime.record import PrimitiveType


class ContractsLibrary:
    def __init__(self, query: QueryEngine) -> None:
        self.query = query

    def commitments(self):
        return self.query.query({"type": PrimitiveType.COMMITMENT})
