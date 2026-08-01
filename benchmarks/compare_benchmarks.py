from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


THROUGHPUT_KEYS = ("append_records_per_sec", "verify_records_per_sec")
LATENCY_KEYS = (
    "graph_descendants_sec",
    "authorization_verify_sec",
    "query_latency_ms",
    "replay_sec",
    "memory_peak_mb",
    "disk_usage_bytes",
)


def _pct_change(base: float, current: float) -> float:
    if base == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - base) / base) * 100.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare benchmark JSON outputs.")
    parser.add_argument("--baseline", required=True, help="path to baseline benchmark JSON")
    parser.add_argument("--current", required=True, help="path to current benchmark JSON")
    parser.add_argument(
        "--throughput-regression-pct",
        type=float,
        default=10.0,
        help="fail threshold for throughput decreases in percent",
    )
    parser.add_argument(
        "--latency-regression-pct",
        type=float,
        default=15.0,
        help="fail threshold for latency/memory/disk increases in percent",
    )
    args = parser.parse_args()

    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    current = json.loads(Path(args.current).read_text(encoding="utf-8"))

    baseline_results = baseline["results"]
    current_results = current["results"]
    backends = sorted(set(baseline_results.keys()) & set(current_results.keys()))

    failures: list[str] = []
    print(f"Baseline: {args.baseline}")
    print(f"Current : {args.current}")
    print()

    for backend in backends:
        print(f"[{backend}]")
        base_metrics = baseline_results[backend]
        cur_metrics = current_results[backend]
        keys = list(THROUGHPUT_KEYS) + list(LATENCY_KEYS)
        for key in keys:
            base_value = float(base_metrics[key])
            cur_value = float(cur_metrics[key])
            delta_pct = _pct_change(base_value, cur_value)
            direction = "better"
            if key in THROUGHPUT_KEYS:
                # Higher is better for throughput.
                if delta_pct < 0:
                    direction = "worse"
                if delta_pct <= -abs(args.throughput_regression_pct):
                    failures.append(
                        f"{backend}:{key} regressed {delta_pct:.2f}% (threshold {-abs(args.throughput_regression_pct):.2f}%)"
                    )
            else:
                # Lower is better for latency/memory/disk.
                if delta_pct > 0:
                    direction = "worse"
                if delta_pct >= abs(args.latency_regression_pct):
                    failures.append(
                        f"{backend}:{key} regressed +{delta_pct:.2f}% (threshold +{abs(args.latency_regression_pct):.2f}%)"
                    )
            print(f"  {key}: base={base_value:.6g} current={cur_value:.6g} delta={delta_pct:+.2f}% ({direction})")
        print()

    if failures:
        print("Regressions detected:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("No regressions beyond thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
