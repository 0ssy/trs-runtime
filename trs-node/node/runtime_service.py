from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from runtime.record import PrimitiveType, Record
from runtime.replay import ReplayEngine
from runtime.terranode_adapter import TerraNodeRuntimeAdapter


@dataclass(frozen=True)
class SubmitOutcome:
    accepted: bool
    record_id: str
    errors: list[str]


@dataclass(frozen=True)
class SyncOutcome:
    accepted_count: int
    rejected_count: int
    appended_ids: list[str]
    rejected_errors: list[list[str]]


class RuntimeService:
    def __init__(self) -> None:
        self.adapter = TerraNodeRuntimeAdapter()
        self.replay_engine = ReplayEngine(self.adapter.store)

    def submit(self, envelope: Mapping[str, Any]) -> SubmitOutcome:
        result = self.adapter.submit_envelope(envelope)
        return SubmitOutcome(
            accepted=result.accepted,
            record_id=str(envelope.get("id", "")),
            errors=list(result.verification.errors),
        )

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        return self.adapter.query(expression)

    def sync(self, records: list[Mapping[str, Any]]) -> SyncOutcome:
        incoming = [self._record_from_envelope(envelope) for envelope in records]
        result = self.adapter.sync_incoming(incoming)
        rejected_errors = [verification.errors for verification in result.verification_results if not verification.valid]
        return SyncOutcome(
            accepted_count=len(result.appended_ids),
            rejected_count=len(rejected_errors),
            appended_ids=list(result.appended_ids),
            rejected_errors=rejected_errors,
        )

    def replay(self) -> dict[str, Any]:
        snapshot = self.replay_engine.replay()
        return {
            "identities": snapshot.identities,
            "workflows": snapshot.workflows,
            "contracts": snapshot.contracts,
            "reputation": snapshot.reputation,
            "coordination": {
                "intention_to_commitments": snapshot.coordination.intention_to_commitments,
                "unresolved_intentions": snapshot.coordination.unresolved_intentions,
                "orphan_commitments": snapshot.coordination.orphan_commitments,
            },
        }

    def _record_from_envelope(self, envelope: Mapping[str, Any]) -> Record:
        required = ("id", "type", "author", "timestamp", "schema", "payload", "signature")
        missing = [key for key in required if key not in envelope]
        if missing:
            raise ValueError(f"record missing required fields: {', '.join(missing)}")
        primitive = PrimitiveType(str(envelope["type"]))
        timestamp = envelope["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp must be ISO string or datetime")
        payload = envelope["payload"]
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be an object")
        causes_raw = envelope.get("causes", [])
        auth_raw = envelope.get("authorization", [])
        if not isinstance(causes_raw, list) or not isinstance(auth_raw, list):
            raise ValueError("causes and authorization must be lists")
        return Record(
            id=str(envelope["id"]),
            type=primitive,
            author=str(envelope["author"]),
            timestamp=timestamp,
            schema=str(envelope["schema"]),
            payload=payload,
            causes=tuple(str(value) for value in causes_raw),
            authorization=tuple(str(value) for value in auth_raw),
            signature=str(envelope["signature"]),
            subject=str(envelope.get("subject", "")),
        )
