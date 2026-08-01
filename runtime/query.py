from __future__ import annotations

from typing import Any, Mapping

from .record import Record
from .storage import StorageEngine


class QueryEngine:
    def __init__(self, store: StorageEngine) -> None:
        self.store = store

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        return self.store.query(expression)
