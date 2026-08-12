from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import derive_record_id


class PrimitiveType(str, Enum):
    OBSERVATION = "Observation"
    COMMITMENT = "Commitment"
    INTENTION = "Intention"


_SCALAR_TYPES = (str, int, float, bool, bytes, type(None))


def _freeze(value: Any) -> Any:
    value_type = type(value)
    if value_type in _SCALAR_TYPES:
        return value
    if value_type is dict:
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if value_type is list:
        return tuple(_freeze(v) for v in value)
    if value_type is set:
        return frozenset(_freeze(v) for v in value)
    if value_type is tuple:
        return tuple(_freeze(v) for v in value)
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
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
    subject: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("record id is required")
        if not self.author:
            raise ValueError("author is required")
        if not self.schema:
            raise ValueError("schema is required")
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc))
        if not self.subject:
            object.__setattr__(self, "subject", self.causes[0] if self.causes else self.id)

        object.__setattr__(self, "payload", _freeze(self.payload))
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
        subject: str | None = None,
    ) -> "Record":
        # Explicit primitive declaration is required. No payload-based inference.
        if not isinstance(primitive_type, PrimitiveType):
            raise ValueError("invalid primitive type")
        draft = Record(
            id=record_id or "__pending_record_id__",
            type=primitive_type,
            author=author,
            timestamp=timestamp or datetime.now(timezone.utc),
            schema=schema,
            payload=payload,
            causes=causes,
            authorization=authorization,
            signature=signature,
            subject=subject or (causes[0] if causes else "__self__"),
        )
        generated_id = derive_record_id(draft)
        return Record(
            id=record_id or generated_id,
            type=primitive_type,
            author=author,
            timestamp=draft.timestamp,
            schema=schema,
            payload=payload,
            causes=causes,
            authorization=authorization,
            signature=signature,
            subject=subject or (causes[0] if causes else record_id or generated_id),
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
            "subject": self.subject,
        }


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    if isinstance(value, frozenset):
        return sorted(_to_plain(v) for v in value)
    return value
