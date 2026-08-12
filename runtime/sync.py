from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from dataclasses import dataclass

from .canonical import canonical_record_bytes
from .record import PrimitiveType, Record
from .storage import StorageEngine
from .verifier import VerificationResult, Verifier


def _hash_record(record: Record) -> str:
    payload = canonical_record_bytes(record, include_signature=True)
    return hashlib.sha256(payload).hexdigest()


def checkpoint_inventory_hash(store: StorageEngine) -> str:
    inventory = hash_inventory(store)
    serialized = "|".join(f"{record_id}:{record_hash}" for record_id, record_hash in sorted(inventory.items()))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def head_record_ids(store: StorageEngine) -> list[str]:
    records = store.all()
    referenced: set[str] = set()
    for record in records:
        referenced.update(record.causes)
    return sorted(record.id for record in records if record.id not in referenced)


def build_checkpoint_record(
    store: StorageEngine,
    *,
    author: str,
    timestamp: datetime | None = None,
    signature: str = "",
    record_id: str | None = None,
) -> Record:
    heads = head_record_ids(store)
    checkpoint_payload = {
        "subject": "trs.checkpoint",
        "value": {
            "inventory_hash": checkpoint_inventory_hash(store),
            "heads": heads,
        },
    }
    return Record.create(
        primitive_type=PrimitiveType.OBSERVATION,
        author=author,
        timestamp=timestamp or datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload=checkpoint_payload,
        causes=tuple(heads),
        signature=signature,
        record_id=record_id,
        subject="trs.checkpoint",
    )


def hash_inventory(store: StorageEngine) -> dict[str, str]:
    return {record.id: _hash_record(record) for record in store.all()}


def missing_records(local_store: StorageEngine, remote_records: list[Record]) -> list[Record]:
    return [record for record in remote_records if not local_store.exists(record.id)]


@dataclass(frozen=True)
class SyncResult:
    appended_ids: list[str]
    verification_results: list[VerificationResult]


def sync_append_only(
    local_store: StorageEngine, incoming_records: list[Record], verifier: Verifier
) -> SyncResult:
    appended_ids: list[str] = []
    verification_results: list[VerificationResult] = []
    for record in missing_records(local_store, incoming_records):
        result = verifier.verify(record)
        verification_results.append(result)
        if result.valid:
            local_store.append(record)
            appended_ids.append(record.id)
    return SyncResult(appended_ids=appended_ids, verification_results=verification_results)
