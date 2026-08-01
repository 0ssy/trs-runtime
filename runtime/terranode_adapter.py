from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from .crypto import CryptoSuite
from .graph import Graph
from .query import QueryEngine
from .record import PrimitiveType, Record
from .storage import RecordStore, StorageEngine
from .sync import SyncResult, sync_append_only
from .verifier import VerificationResult, Verifier


@dataclass(frozen=True)
class SubmitResult:
    accepted: bool
    verification: VerificationResult


class TerraNodeRuntimeAdapter:
    """
    TerraNode integration boundary.

    TerraNode provides envelopes and receives runtime results without
    embedding TRS rule logic in TerraNode itself.
    """

    def __init__(self, store: StorageEngine | None = None, crypto: CryptoSuite | None = None) -> None:
        self.store = store or RecordStore()
        self.verifier = Verifier(self.store, crypto=crypto)
        self.graph = Graph(self.store)
        self.query_engine = QueryEngine(self.store)

    def submit_envelope(self, envelope: Mapping[str, Any]) -> SubmitResult:
        record = self._record_from_envelope(envelope)
        verification = self.verifier.verify(record)
        if verification.valid:
            self.store.append(record)
        return SubmitResult(accepted=verification.valid, verification=verification)

    def get_record(self, record_id: str) -> Record | None:
        return self.store.get(record_id)

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        return self.query_engine.query(expression)

    def parents(self, record_id: str) -> list[str]:
        return self.graph.parents(record_id)

    def children(self, record_id: str) -> list[str]:
        return self.graph.children(record_id)

    def sync_incoming(self, incoming_records: list[Record]) -> SyncResult:
        return sync_append_only(self.store, incoming_records, self.verifier)

    def _record_from_envelope(self, envelope: Mapping[str, Any]) -> Record:
        required = ("id", "type", "author", "timestamp", "schema", "payload", "signature")
        missing = [key for key in required if key not in envelope]
        if missing:
            raise ValueError(f"envelope missing required fields: {', '.join(missing)}")

        primitive = PrimitiveType(envelope["type"])
        timestamp = envelope["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        if not isinstance(timestamp, datetime):
            raise ValueError("timestamp must be ISO string or datetime")

        causes = envelope.get("causes", [])
        authorization = envelope.get("authorization", [])
        return Record(
            id=str(envelope["id"]),
            type=primitive,
            author=str(envelope["author"]),
            timestamp=timestamp,
            schema=str(envelope["schema"]),
            payload=envelope["payload"],
            causes=tuple(str(value) for value in causes),
            authorization=tuple(str(value) for value in authorization),
            signature=str(envelope["signature"]),
        )
