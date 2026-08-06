from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from implementation import TRSRuntime


def run_vector(path: Path, category: str, expected: dict) -> dict:
    vector = json.loads(path.read_text(encoding="utf-8"))
    runtime = TRSRuntime()
    verified: list[str] = []
    failed: list[str] = []
    errors: list[str] = []
    if category == "replay":
        imported = runtime.import_unordered(vector["records"])
        errors.extend(f"{rid}: {msg}" for rid, values in imported["errors"].items() for msg in values)
        replay = runtime.replay()
        exp = expected.get(vector["vector_id"], {}).get("expect", {})
        unresolved = exp.get("coordination.unresolved_intentions_contains", [])
        links = exp.get("coordination.intention_to_commitments_contains", {})
        ok = not imported["rejected_ids"] and all(x in replay["unresolved_intentions"] for x in unresolved) and all(all(y in replay["intention_to_commitments"].get(x, []) for y in ys) for x, ys in links.items())
        return {"vector_id": vector["vector_id"], "status": "pass" if ok else "fail", "details": {"verified_records": [r["id"] for r in imported["imported_records"]], "failed_records": imported["rejected_ids"], "errors": errors, "replay": replay}}
    if category == "authorization":
        for record in vector["records"]:
            result = runtime.append(record)
            (verified if result.valid else failed).append(record["id"])
            errors.extend(result.errors)
        target = vector["target_record_id"]
        target_record = runtime.get(target)
        path_ids: list[str] = []
        if target_record:
            stack = list(target_record.get("authorization", []))
            seen: set[str] = set()
            while stack:
                rid = stack.pop()
                if rid in seen:
                    continue
                seen.add(rid)
                path_ids.append(rid)
                parent = runtime.get(rid)
                if parent:
                    stack.extend(parent.get("authorization", []))
                    stack.extend(parent.get("causes", []))
        exp = expected.get(vector["vector_id"], {}).get("expect", {})
        ok = not failed and all(x in path_ids for x in exp.get("authorization_path_contains", []))
        return {"vector_id": vector["vector_id"], "status": "pass" if ok else "fail", "details": {"verified_records": verified, "failed_records": failed, "errors": errors, "authorization_path": path_ids}}
    for record in vector["records"]:
        result = runtime.append(record)
        (verified if result.valid else failed).append(record["id"])
        errors.extend(result.errors)
    exp = expected.get(vector["vector_id"], {})
    if category == "valid":
        ok = not failed and all(x in verified for x in exp.get("records_valid", []))
        if exp.get("conflict_expectation"):
            ok = ok and runtime.conflict_visible()
    else:
        must_fail = set(exp.get("must_fail_records", []))
        ok = must_fail.issubset(set(failed)) and all(any(fragment in error for error in errors) for fragment in exp.get("error_contains", []))
    return {"vector_id": vector["vector_id"], "status": "pass" if ok else "fail", "details": {"verified_records": verified, "failed_records": failed, "errors": errors, "conflict_visible": runtime.conflict_visible()}}


def main() -> int:
    vectors_root = ROOT / "trs-conformance"
    index = json.loads((vectors_root / "vectors" / "index.json").read_text(encoding="utf-8"))
    results: list[dict] = []
    for category, paths in index.items():
        expected_path = vectors_root / "expected" / f"{category}.expected.json"
        expected = json.loads(expected_path.read_text(encoding="utf-8")) if expected_path.exists() else {}
        for relative in paths:
            results.append(run_vector(vectors_root / relative, category, expected))
    out = {"implementation_name": "impl-0001-independent-python", "implementation_version": "0.1.0", "status": "pass" if all(r["status"] == "pass" for r in results) else "fail", "results": results}
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "conformance-results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if out["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
