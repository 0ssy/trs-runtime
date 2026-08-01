from __future__ import annotations

from runtime.query import QueryEngine


class CapabilitiesLibrary:
    def __init__(self, query: QueryEngine) -> None:
        self.query = query

    def by_authorization(self, record_id: str):
        return self.query.query({"authorization": record_id})
