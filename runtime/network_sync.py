from __future__ import annotations

from dataclasses import dataclass

from .record import Record
from .storage import StorageEngine
from .sync import hash_inventory, missing_records
from .verifier import VerificationResult, Verifier


@dataclass(frozen=True)
class NetworkSyncResult:
    missing_ids: list[str]
    appended_ids: list[str]
    rejected_ids: list[str]
    verification_results: list[VerificationResult]


def sync_nodes(source: StorageEngine, target: StorageEngine, target_verifier: Verifier) -> NetworkSyncResult:
    source_inventory = hash_inventory(source)
    target_inventory = hash_inventory(target)
    missing_ids = [
        record_id
        for record_id, source_hash in source_inventory.items()
        if target_inventory.get(record_id) != source_hash
    ]
    incoming = [record for record in (source.get(record_id) for record_id in missing_ids) if record is not None]
    append_result = ingest_records_unordered(target, incoming, target_verifier)
    return NetworkSyncResult(
        missing_ids=missing_ids,
        appended_ids=append_result.appended_ids,
        rejected_ids=append_result.rejected_ids,
        verification_results=append_result.verification_results,
    )


@dataclass(frozen=True)
class UnorderedIngestResult:
    appended_ids: list[str]
    rejected_ids: list[str]
    verification_results: list[VerificationResult]


def ingest_records_unordered(
    target: StorageEngine, incoming_records: list[Record], target_verifier: Verifier
) -> UnorderedIngestResult:
    pending = missing_records(target, incoming_records)
    appended_ids: list[str] = []
    rejected_ids: list[str] = []
    last_results: dict[str, VerificationResult] = {}

    while pending:
        progress = False
        next_pending: list[Record] = []
        for record in pending:
            if target.exists(record.id):
                continue
            verification = target_verifier.verify(record)
            last_results[record.id] = verification
            if verification.valid:
                target.append(record)
                appended_ids.append(record.id)
                progress = True
                continue

            if _is_dependency_wait(verification):
                next_pending.append(record)
            else:
                rejected_ids.append(record.id)

        if not progress:
            for record in next_pending:
                rejected_ids.append(record.id)
            break
        pending = next_pending

    return UnorderedIngestResult(
        appended_ids=appended_ids,
        rejected_ids=rejected_ids,
        verification_results=[last_results[rid] for rid in (*appended_ids, *rejected_ids) if rid in last_results],
    )


def _is_dependency_wait(verification: VerificationResult) -> bool:
    wait_markers = (
        "missing causes",
        "missing authorization records",
        "missing delegation path to genesis",
    )
    return any(any(marker in error for marker in wait_markers) for error in verification.errors)
