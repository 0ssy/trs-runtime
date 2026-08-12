from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .canonical import canonical_record_bytes
from .record import Record
from .storage import StorageEngine
from .verifier import VerificationResult, Verifier


def _hash_record(record: Record) -> str:
    payload = canonical_record_bytes(record, include_signature=True)
    return hashlib.sha256(payload).hexdigest()


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
