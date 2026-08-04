from __future__ import annotations

from typing import Any

from .exceptions import TRSValidationError
from .models import HealthStatus, SubmitResult, SyncResult
from .serialization import ensure_array, ensure_object, parse_health, parse_submit, parse_sync
from .transport import HTTPTransport


class Client:
    def __init__(self, base_url: str, *, timeout_seconds: float = 5.0, transport: HTTPTransport | None = None) -> None:
        self.transport = transport or HTTPTransport(base_url, timeout_seconds=timeout_seconds)

    def health(self) -> HealthStatus:
        return parse_health(self.transport.get("/health"))

    def submit(self, record: dict[str, Any]) -> SubmitResult:
        result = parse_submit(self.transport.post("/submit", {"record": record}))
        if not result.accepted:
            raise TRSValidationError("record rejected by verifier", errors=result.errors)
        return result

    def query(self, expression: dict[str, Any]) -> list[dict[str, Any]]:
        payload = ensure_object(self.transport.post("/query", {"query": expression}), "query response")
        records = ensure_array(payload.get("records", []), "records")
        parsed: list[dict[str, Any]] = []
        for item in records:
            parsed.append(ensure_object(item, "record"))
        return parsed

    def sync(self, records: list[dict[str, Any]]) -> SyncResult:
        return parse_sync(self.transport.post("/sync", {"records": records}))

    def replay(self) -> dict[str, Any]:
        return ensure_object(self.transport.post("/replay", {}), "replay response")

