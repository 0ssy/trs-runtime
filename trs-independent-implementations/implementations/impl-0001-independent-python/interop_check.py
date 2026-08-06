from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from implementation import TRSRuntime


def main() -> int:
    latest = ROOT / "evidence" / "interop" / "cycle0012_latest.json"
    if not latest.exists():
        raise SystemExit("missing baseline interop summary; run the repository baseline first")
    summary = json.loads(latest.read_text(encoding="utf-8"))
    fixture = ROOT / summary["fixture_path"]
    records = json.loads(fixture.read_text(encoding="utf-8"))["records"]
    runtime = TRSRuntime()
    result = runtime.import_unordered(records)
    source_hash = summary["source_hash"]
    imported_hash = __import__("hashlib").sha256(json.dumps(result["inventory"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    out = {
        "implementation_name": "impl-0001-independent-python",
        "fixture_path": str(fixture.relative_to(ROOT)),
        "source_count": len(records),
        "imported_count": len(result["imported_records"]),
        "rejected_ids": result["rejected_ids"],
        "inventory_hash_match": source_hash == imported_hash,
        "conflict_visible": result["conflict_visible"],
        "unresolved_intentions": result["unresolved_intentions"],
        "details": result["errors"],
    }
    out["status"] = "pass" if out["imported_count"] == out["source_count"] and not out["rejected_ids"] and out["inventory_hash_match"] and out["conflict_visible"] else "fail"
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "interop-results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if out["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
