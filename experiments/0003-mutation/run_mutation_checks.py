from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.mutation_checks import run_mutation_checks


def main() -> int:
    summary = run_mutation_checks()
    payload = {
        "total": summary.total,
        "killed": summary.killed,
        "survived": summary.survived,
        "results": [
            {"mutant": item.mutant, "killed": item.killed, "details": item.details}
            for item in summary.results
        ],
    }
    print(json.dumps(payload, indent=2))
    out_path = Path("evidence") / "test_runs" / "2026-08-01_mutation_checks.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if summary.survived == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
