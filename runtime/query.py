from __future__ import annotations

from typing import Any, Mapping

from .record import PrimitiveType, Record
from .storage import RecordStore


class QueryEngine:
    def __init__(self, store: RecordStore) -> None:
        self.store = store

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        records = self.store.all()
        for key, value in expression.items():
            if key == "type":
                primitive = value if isinstance(value, PrimitiveType) else PrimitiveType(value)
                records = [r for r in records if r.type == primitive]
            elif key == "author":
                records = [r for r in records if r.author == value]
            elif key == "schema":
                records = [r for r in records if r.schema == value]
            elif key == "cause":
                records = [r for r in records if value in r.causes]
            elif key == "authorization":
                records = [r for r in records if value in r.authorization]
            else:
                raise ValueError(f"unsupported query key: {key}")
        return records
