from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .record import Record


_HASH_DOMAIN_PREFIX = b"TRS-HASH-1\n"
_SELF_SUBJECT_SENTINEL = "__self__"


def canonical_json_bytes(value: Any) -> bytes:
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_record_bytes(record: "Record", *, include_signature: bool = True) -> bytes:
    envelope = record.to_dict()
    if not include_signature:
        envelope.pop("signature", None)
    return canonical_json_bytes(envelope)


def canonical_record_identity_bytes(record: "Record") -> bytes:
    envelope = record.to_dict()
    envelope.pop("id", None)
    envelope.pop("signature", None)
    if not record.causes and record.subject == record.id:
        envelope["subject"] = _SELF_SUBJECT_SENTINEL
    return canonical_json_bytes(envelope)


def derive_record_id(record: "Record") -> str:
    digest = hashlib.sha256(_HASH_DOMAIN_PREFIX + canonical_record_identity_bytes(record)).hexdigest()
    return f"sha256:{digest}"


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            normalized[key] = _normalize(item)
        return normalized
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON numbers must be finite")
        return value
    raise TypeError(f"unsupported canonical JSON type: {type(value).__name__}")
