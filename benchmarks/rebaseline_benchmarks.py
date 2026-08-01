from __future__ import annotations

import argparse
from argparse import Namespace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks.gate_benchmarks import median_payload, resolve_gate_config
from runtime.benchmark import run_benchmarks


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-capture and archive benchmark baseline using median-of-N runs.")
    parser.add_argument(
        "--mode",
        choices=["quick", "dev", "pr", "ci", "nightly"],
        default="nightly",
        help="preset benchmark mode for baseline capture",
    )
    parser.add_argument("--records", type=int, default=None, help="record count override")
    parser.add_argument("--runs", type=int, default=None, help="run count override for median baseline")
    parser.add_argument(
        "--baseline",
        type=str,
        default="evidence/benchmarks/2026-08-01_phase15_baseline.json",
        help="baseline JSON file to write",
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default="evidence/benchmarks/archive",
        help="directory for archived prior baseline artifacts",
    )
    parser.add_argument(
        "--history-dir",
        type=str,
        default="benchmarks/history",
        help="directory to persist each baseline-capture run artifact",
    )
    args = parser.parse_args()

    config = resolve_gate_config(
        Namespace(
            mode=args.mode,
            records=args.records,
            runs=args.runs,
            throughput_regression_pct=None,
            latency_regression_pct=None,
        )
    )
    if int(config["runs"]) < 1:
        raise ValueError("--runs must be >= 1")

    history_dir = Path(args.history_dir)
    history_dir.mkdir(parents=True, exist_ok=True)

    run_payloads: list[dict] = []
    for run_index in range(1, int(config["runs"]) + 1):
        run_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "records": int(config["records"]),
            "run_index": run_index,
            "results": run_benchmarks(records=int(config["records"])),
        }
        run_payloads.append(run_payload)
        run_name = (
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_rebaseline_records-{int(config['records'])}_run-{run_index}.json"
        )
        (history_dir / run_name).write_text(json.dumps(run_payload, indent=2), encoding="utf-8")

    baseline_payload = median_payload(run_payloads, records=int(config["records"]))
    baseline_payload["mode"] = args.mode

    baseline_path = Path(args.baseline)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    if baseline_path.exists():
        archive_dir = Path(args.archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_name = f"{baseline_path.stem}_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}.json"
        (archive_dir / archive_name).write_text(baseline_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Archived previous baseline: {archive_dir / archive_name}")

    baseline_path.write_text(json.dumps(baseline_payload, indent=2), encoding="utf-8")
    print(f"New baseline: {baseline_path}")
    print(f"Mode: {args.mode} | Records: {int(config['records'])} | Runs: {int(config['runs'])} (median)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
