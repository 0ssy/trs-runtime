from __future__ import annotations

from runtime.query import QueryEngine


class IdentityLibrary:
    def __init__(self, query: QueryEngine) -> None:
        self.query = query

    def by_author(self, author: str):
        return self.query.query({"author": author})
