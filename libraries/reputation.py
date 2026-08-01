from __future__ import annotations

from collections import Counter

from runtime.query import QueryEngine


class ReputationLibrary:
    def __init__(self, query: QueryEngine) -> None:
        self.query = query

    def author_activity(self) -> dict[str, int]:
        counts = Counter(record.author for record in self.query.query({}))
        return dict(counts)
