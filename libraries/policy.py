from __future__ import annotations

from runtime.query import QueryEngine


class PolicyLibrary:
    def __init__(self, query: QueryEngine) -> None:
        self.query = query

    def by_schema(self, schema: str):
        return self.query.query({"schema": schema})
