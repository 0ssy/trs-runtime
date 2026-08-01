from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.benchmark import run_benchmarks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TRS runtime benchmarks")
    parser.add_argument("--records", type=int, default=2000, help="number of records to benchmark")
    parser.add_argument("--out", type=str, default="", help="optional output JSON path")
    args = parser.parse_args()

    results = run_benchmarks(records=args.records)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "records": args.records,
        "results": results,
    }
    print(json.dumps(payload, indent=2))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
