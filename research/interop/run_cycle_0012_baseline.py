from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.network_sync import ingest_records_unordered
from runtime.record import PrimitiveType, Record
from runtime.replay import ReplayEngine
from runtime.storage import RecordStore
from runtime.sync import hash_inventory
from runtime.verifier import RuleStatus, Verifier
from terranode.terranode.policy import ProRataPolicy
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter
EVIDENCE_DIR = ROOT / "evidence" / "interop"
LATEST_PATH = EVIDENCE_DIR / "cycle0012_latest.json"


@dataclass(frozen=True)
class BaselineResult:
    fixture_path: str
    summary_path: str
    source_count: int
    imported_count: int
    rejected_ids: list[str]
    source_hash: str
    imported_hash: str
    conflict_visible: bool
    replay_unresolved_intentions: list[str]
    frozen_doc_hashes: dict[str, str]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(64 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _frozen_doc_hashes() -> dict[str, str]:
    candidates = [
        ROOT / "docs" / "TRS-v1.0.pdf",
        ROOT / "docs" / "DesignRecord.pdf",
        ROOT / "docs" / "Amendment_Log.md",
    ]
    hashes: dict[str, str] = {}
    for path in candidates:
        if path.exists():
            hashes[str(path.relative_to(ROOT))] = _sha256_file(path)
        else:
            hashes[str(path.relative_to(ROOT))] = "MISSING"
    return hashes


def _record_from_dict(data: dict[str, object]) -> Record:
    timestamp_raw = data["timestamp"]
    if not isinstance(timestamp_raw, str):
        raise ValueError("timestamp must be string")
    return Record(
        id=str(data["id"]),
        type=PrimitiveType(str(data["type"])),
        author=str(data["author"]),
        timestamp=datetime.fromisoformat(timestamp_raw),
        schema=str(data["schema"]),
        payload=dict(data["payload"]) if isinstance(data["payload"], dict) else {},
        causes=tuple(str(value) for value in data.get("causes", [])),
        authorization=tuple(str(value) for value in data.get("authorization", [])),
        signature=str(data["signature"]),
        subject=str(data.get("subject", "")),
    )


def run_cycle_0012_baseline() -> BaselineResult:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

    adapter = TerraNodeRuntimeAdapter(node_id="cycle0012-ref")
    alice = adapter.submit_intention("alice", "warehouse-7", 80.0, 100.0)
    bob = adapter.submit_intention("bob", "warehouse-7", 60.0, 100.0)
    if not alice.verification.valid or not bob.verification.valid:
        raise RuntimeError("reference fixture creation failed")
    pre_allocation_conflicts = adapter.find_conflicts("warehouse-7")
    decision = ProRataPolicy().allocate(pre_allocation_conflicts)
    adapter.apply_allocations(decision)

    source_records = sorted((record.to_dict() for record in adapter.store.all()), key=lambda item: str(item["id"]))
    fixture_path = EVIDENCE_DIR / f"{timestamp}_cycle0012_fixture.json"
    fixture_path.write_text(json.dumps({"records": source_records}, indent=2), encoding="utf-8")

    target_store = RecordStore()
    target_verifier = Verifier(target_store)
    imported_records = [_record_from_dict(item) for item in source_records]
    ingest = ingest_records_unordered(target_store, imported_records, target_verifier)

    source_inventory = hash_inventory(adapter.store)
    target_inventory = hash_inventory(target_store)

    replay = ReplayEngine(target_store).replay()
    conflict_visible = False
    for record in target_store.all():
        if record.type != PrimitiveType.INTENTION:
            continue
        rule = target_verifier.verify_non_silent_conflict(record)
        if rule.status == RuleStatus.PASS and "conflict explicitly visible" in rule.reason:
            conflict_visible = True
            break
    result = BaselineResult(
        fixture_path=str(fixture_path.relative_to(ROOT)),
        summary_path="",
        source_count=len(source_records),
        imported_count=len(list(target_store.all())),
        rejected_ids=list(ingest.rejected_ids),
        source_hash=hashlib.sha256(
            json.dumps(source_inventory, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        imported_hash=hashlib.sha256(
            json.dumps(target_inventory, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        conflict_visible=conflict_visible,
        replay_unresolved_intentions=list(replay.coordination.unresolved_intentions),
        frozen_doc_hashes=_frozen_doc_hashes(),
    )
    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0012_summary.json"
    summary = asdict(result) | {"summary_path": str(summary_path.relative_to(ROOT))}
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return BaselineResult(**summary)


if __name__ == "__main__":
    outcome = run_cycle_0012_baseline()
    print(f"Fixture: {outcome.fixture_path}")
    print(f"Summary: {outcome.summary_path}")
    print(f"Counts: source={outcome.source_count} imported={outcome.imported_count}")
    print(f"Rejected: {outcome.rejected_ids}")
    print(f"Inventory hash match: {outcome.source_hash == outcome.imported_hash}")
    print(f"Conflict visible: {outcome.conflict_visible}")
    print(f"Replay unresolved intentions: {outcome.replay_unresolved_intentions}")
