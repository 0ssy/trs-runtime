from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.interop.independent_impl.engine import IndependentInteropEngine

EVIDENCE_DIR = ROOT / "evidence" / "interop"
LATEST_BASELINE = EVIDENCE_DIR / "cycle0012_latest.json"
LATEST_CROSS = EVIDENCE_DIR / "cycle0012_cross_latest.json"


@dataclass(frozen=True)
class CrossImplResult:
    baseline_summary_path: str
    fixture_path: str
    source_count: int
    imported_count: int
    rejected_ids: list[str]
    inventory_hash_match: bool
    conflict_visible: bool
    unresolved_intentions: list[str]
    independent_shape_errors: dict[str, list[str]]
    independent_dependency_errors: dict[str, list[str]]


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cycle_0012_cross_impl() -> CrossImplResult:
    if not LATEST_BASELINE.exists():
        raise RuntimeError("missing baseline summary: run run_cycle_0012_baseline.py first")
    baseline = _load_json(LATEST_BASELINE)
    fixture_rel = baseline["fixture_path"]
    if not isinstance(fixture_rel, str):
        raise RuntimeError("baseline fixture path is invalid")
    fixture_path = ROOT / fixture_rel
    fixture = _load_json(fixture_path)
    records = fixture.get("records")
    if not isinstance(records, list):
        raise RuntimeError("fixture missing records list")

    engine = IndependentInteropEngine()
    result = engine.import_unordered(records)

    source_inventory_hash = baseline.get("source_hash")
    independent_inventory_hash = hashlib.sha256(
        json.dumps(result.inventory, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    out = CrossImplResult(
        baseline_summary_path=str(LATEST_BASELINE.relative_to(ROOT)),
        fixture_path=str(fixture_path.relative_to(ROOT)),
        source_count=len(records),
        imported_count=len(result.imported_records),
        rejected_ids=result.rejected_ids,
        inventory_hash_match=source_inventory_hash == independent_inventory_hash,
        conflict_visible=result.conflict_visible,
        unresolved_intentions=result.unresolved_intentions,
        independent_shape_errors=result.shape_errors,
        independent_dependency_errors=result.dependency_errors,
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0012_cross_impl_summary.json"
    summary_path.write_text(json.dumps(asdict(out), indent=2), encoding="utf-8")
    LATEST_CROSS.write_text(json.dumps(asdict(out), indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    result = run_cycle_0012_cross_impl()
    print(f"Fixture: {result.fixture_path}")
    print(f"Imported: {result.imported_count}/{result.source_count}")
    print(f"Rejected: {result.rejected_ids}")
    print(f"Inventory hash match: {result.inventory_hash_match}")
    print(f"Conflict visible: {result.conflict_visible}")
    print(f"Unresolved intentions: {result.unresolved_intentions}")
