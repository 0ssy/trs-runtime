from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Program 5: scale campaign for TRS runtime.")
    parser.add_argument(
        "--records",
        type=int,
        nargs="+",
        default=[10_000, 100_000],
        help="record scales to benchmark",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/program5_scale_latest.json",
        help="output JSON path",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=900,
        help="per-scale-per-backend timeout in seconds",
    )
    parser.add_argument(
        "--backends",
        type=str,
        nargs="+",
        default=["in_memory", "sqlite", "lmdb", "rocksdb"],
        help="backends to benchmark",
    )
    args = parser.parse_args()

    runs: list[dict] = []
    for record_count in args.records:
        print(f"[Program 5] Running scale={int(record_count)} records...")
        backend_runs: list[dict] = []
        with tempfile.TemporaryDirectory(prefix="trs-scale-") as tmp:
            for backend in args.backends:
                run_out = Path(tmp) / f"scale-{int(record_count)}-{backend}.json"
                cmd = [
                    sys.executable,
                    "benchmarks/run_benchmarks.py",
                    "--records",
                    str(int(record_count)),
                    "--backend",
                    backend,
                    "--out",
                    str(run_out),
                ]
                try:
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=int(args.timeout_sec))
                except subprocess.TimeoutExpired:
                    backend_runs.append(
                        {
                            "backend": backend,
                            "status": "timeout",
                            "error": f"timed out after {int(args.timeout_sec)}s",
                        }
                    )
                    continue

                if proc.returncode != 0:
                    backend_runs.append(
                        {
                            "backend": backend,
                            "status": "failed",
                            "error": (proc.stderr or proc.stdout or "").strip()[-2000:],
                        }
                    )
                    continue

                if not run_out.exists():
                    backend_runs.append(
                        {
                            "backend": backend,
                            "status": "failed",
                            "error": "benchmark output file missing",
                        }
                    )
                    continue

                payload = json.loads(run_out.read_text(encoding="utf-8"))
                backend_runs.append(
                    {
                        "backend": backend,
                        "status": "ok",
                        "results": payload["results"],
                    }
                )
        run_status = "ok" if all(item["status"] == "ok" for item in backend_runs) else "partial"
        runs.append(
            {
                "records": int(record_count),
                "status": run_status,
                "backend_runs": backend_runs,
            }
        )

    payload = {
        "program": "Program 5 - Scale",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runs": runs,
        "outcome": "NEED_MORE_EVIDENCE" if any(item.get("status") != "ok" for item in runs) else "TRS survives",
        "note": "Inspect scaling slopes for replay/query/sync surfaces across record counts.",
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote scale campaign artifact: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
