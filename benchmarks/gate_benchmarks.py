from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks.compare_benchmarks import compare_payloads
from runtime.benchmark import run_benchmarks

MODE_PRESETS = {
    "quick": {"records": 80, "runs": 1, "throughput_regression_pct": 20.0, "latency_regression_pct": 30.0},
    "dev": {"records": 120, "runs": 2, "throughput_regression_pct": 15.0, "latency_regression_pct": 25.0},
    "pr": {"records": 120, "runs": 2, "throughput_regression_pct": 15.0, "latency_regression_pct": 25.0},
    "ci": {"records": 200, "runs": 3, "throughput_regression_pct": 10.0, "latency_regression_pct": 15.0},
    "nightly": {"records": 200, "runs": 3, "throughput_regression_pct": 10.0, "latency_regression_pct": 15.0},
}

MODE_THRESHOLD_OVERRIDES: dict[str, dict[str, dict[str, float]]] = {
    "nightly": {
        "in_memory": {
            "append_records_per_sec": 20.0,
            "query_latency_ms": 25.0,
        },
        "sqlite": {
            "authorization_verify_sec": 20.0,
        },
    }
}


def median_payload(run_payloads: list[dict], records: int) -> dict:
    if not run_payloads:
        raise ValueError("at least one run payload is required")

    backends = sorted(run_payloads[0]["results"].keys())
    metrics = sorted(run_payloads[0]["results"][backends[0]].keys())
    median_results: dict[str, dict[str, float]] = {}
    for backend in backends:
        backend_metrics: dict[str, float] = {}
        for metric in metrics:
            samples = [float(payload["results"][backend][metric]) for payload in run_payloads]
            backend_metrics[metric] = statistics.median(samples)
        median_results[backend] = backend_metrics
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "records": records,
        "runs": len(run_payloads),
        "results": median_results,
    }


def resolve_gate_config(args: argparse.Namespace) -> dict[str, float | int]:
    preset = MODE_PRESETS[args.mode]
    records = args.records if args.records is not None else preset["records"]
    runs = args.runs if args.runs is not None else preset["runs"]
    throughput = (
        args.throughput_regression_pct
        if args.throughput_regression_pct is not None
        else preset["throughput_regression_pct"]
    )
    latency = args.latency_regression_pct if args.latency_regression_pct is not None else preset["latency_regression_pct"]
    return {
        "records": int(records),
        "runs": int(runs),
        "throughput_regression_pct": float(throughput),
        "latency_regression_pct": float(latency),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run benchmark and gate regressions against a baseline.")
    parser.add_argument("--mode", choices=sorted(MODE_PRESETS.keys()), default="ci", help="preset benchmark gate mode")
    parser.add_argument("--records", type=int, default=None, help="record count override for benchmark run")
    parser.add_argument(
        "--baseline",
        type=str,
        default="evidence/benchmarks/2026-08-01_phase15_baseline.json",
        help="baseline benchmark JSON path",
    )
    parser.add_argument(
        "--history-dir",
        type=str,
        default="benchmarks/history",
        help="directory to store benchmark history artifacts",
    )
    parser.add_argument("--runs", type=int, default=None, help="number of benchmark runs override for median gating")
    parser.add_argument("--throughput-regression-pct", type=float, default=None)
    parser.add_argument("--latency-regression-pct", type=float, default=None)
    args = parser.parse_args()
    config = resolve_gate_config(args)
    if int(config["runs"]) < 1:
        raise ValueError("--runs must be >= 1")

    baseline_path = Path(args.baseline)
    if not baseline_path.exists():
        raise FileNotFoundError(f"baseline not found: {baseline_path}")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

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
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_records-{int(config['records'])}_run-{run_index}.json"
        )
        (history_dir / run_name).write_text(json.dumps(run_payload, indent=2), encoding="utf-8")

    current = median_payload(run_payloads, records=int(config["records"]))
    artifact_name = (
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_records-{int(config['records'])}_median-of-{int(config['runs'])}.json"
    )
    artifact_path = history_dir / artifact_name
    artifact_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    print(f"Baseline: {baseline_path}")
    print(f"Current : {artifact_path}")
    print(f"Mode    : {args.mode}")
    print(f"Records : {int(config['records'])}")
    print(f"Runs    : {int(config['runs'])} (median)")
    print()
    lines, failures = compare_payloads(
        baseline,
        current,
        throughput_regression_pct=float(config["throughput_regression_pct"]),
        latency_regression_pct=float(config["latency_regression_pct"]),
        threshold_overrides=MODE_THRESHOLD_OVERRIDES.get(args.mode),
    )
    for line in lines:
        print(line)
    if failures:
        print("Regressions detected:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("No regressions beyond thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
