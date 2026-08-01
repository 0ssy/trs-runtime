from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .record import Record


@dataclass
class RecordStore:
    _records: Dict[str, Record] = field(default_factory=dict)
    _append_order: List[str] = field(default_factory=list)
    _children: Dict[str, Set[str]] = field(default_factory=dict)

    def append(self, record: Record) -> None:
        if record.id in self._records:
            raise ValueError(f"record already exists: {record.id}")
        self._records[record.id] = record
        self._append_order.append(record.id)
        for parent_id in record.causes:
            self._children.setdefault(parent_id, set()).add(record.id)

    def get(self, record_id: str) -> Record | None:
        return self._records.get(record_id)

    def exists(self, record_id: str) -> bool:
        return record_id in self._records

    def children(self, record_id: str) -> list[Record]:
        child_ids = self._children.get(record_id, set())
        return [self._records[rid] for rid in self._append_order if rid in child_ids]

    def all(self) -> list[Record]:
        return [self._records[rid] for rid in self._append_order]
