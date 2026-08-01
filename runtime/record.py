from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import uuid


class PrimitiveType(str, Enum):
    OBSERVATION = "Observation"
    COMMITMENT = "Commitment"
    INTENTION = "Intention"


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True, slots=True)
class Record:
    id: str
    type: PrimitiveType
    author: str
    timestamp: datetime
    schema: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    causes: tuple[str, ...] = field(default_factory=tuple)
    authorization: tuple[str, ...] = field(default_factory=tuple)
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("record id is required")
        if not self.author:
            raise ValueError("author is required")
        if not self.schema:
            raise ValueError("schema is required")
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc))

        object.__setattr__(self, "payload", _freeze(dict(self.payload)))
        object.__setattr__(self, "causes", tuple(self.causes))
        object.__setattr__(self, "authorization", tuple(self.authorization))

    @staticmethod
    def create(
        *,
        primitive_type: PrimitiveType,
        author: str,
        schema: str,
        payload: Mapping[str, Any],
        causes: tuple[str, ...] = (),
        authorization: tuple[str, ...] = (),
        signature: str = "",
        record_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> "Record":
        # Explicit primitive declaration is required. No payload-based inference.
        if not isinstance(primitive_type, PrimitiveType):
            raise ValueError("invalid primitive type")
        return Record(
            id=record_id or str(uuid.uuid4()),
            type=primitive_type,
            author=author,
            timestamp=timestamp or datetime.now(timezone.utc),
            schema=schema,
            payload=payload,
            causes=causes,
            authorization=authorization,
            signature=signature,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "schema": self.schema,
            "payload": _to_plain(self.payload),
            "causes": list(self.causes),
            "authorization": list(self.authorization),
            "signature": self.signature,
        }


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    if isinstance(value, frozenset):
        return sorted(_to_plain(v) for v in value)
    return value
