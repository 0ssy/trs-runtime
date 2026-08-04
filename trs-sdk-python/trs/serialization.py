from __future__ import annotations

from typing import Any

from .exceptions import TRSProtocolError
from .models import HealthStatus, SubmitResult, SyncResult


def ensure_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TRSProtocolError(f"{field_name} must be an object")
    return value


def ensure_array(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise TRSProtocolError(f"{field_name} must be an array")
    return value


def parse_health(payload: Any) -> HealthStatus:
    data = ensure_object(payload, "health response")
    return HealthStatus(
        status=str(data.get("status", "")),
        runtime=str(data.get("runtime", "")),
        node=str(data.get("node", "")),
    )


def parse_submit(payload: Any) -> SubmitResult:
    data = ensure_object(payload, "submit response")
    return SubmitResult(
        accepted=bool(data.get("accepted", False)),
        record_id=str(data.get("record_id", "")),
        errors=[str(v) for v in ensure_array(data.get("errors", []), "errors")],
    )


def parse_sync(payload: Any) -> SyncResult:
    data = ensure_object(payload, "sync response")
    rejected_errors_raw = ensure_array(data.get("rejected_errors", []), "rejected_errors")
    rejected_errors = []
    for item in rejected_errors_raw:
        if not isinstance(item, list):
            raise TRSProtocolError("rejected_errors entries must be arrays")
        rejected_errors.append([str(v) for v in item])
    return SyncResult(
        accepted_count=int(data.get("accepted_count", 0)),
        rejected_count=int(data.get("rejected_count", 0)),
        appended_ids=[str(v) for v in ensure_array(data.get("appended_ids", []), "appended_ids")],
        rejected_errors=rejected_errors,
    )

