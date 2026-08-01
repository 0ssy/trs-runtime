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


def compare_payloads(
    baseline: dict,
    current: dict,
    throughput_regression_pct: float = 10.0,
    latency_regression_pct: float = 15.0,
    threshold_overrides: dict[str, dict[str, float]] | None = None,
) -> tuple[list[str], list[str]]:
    baseline_results = baseline["results"]
    current_results = current["results"]
    backends = sorted(set(baseline_results.keys()) & set(current_results.keys()))

    lines: list[str] = []
    failures: list[str] = []
    for backend in backends:
        lines.append(f"[{backend}]")
        base_metrics = baseline_results[backend]
        cur_metrics = current_results[backend]
        keys = list(THROUGHPUT_KEYS) + list(LATENCY_KEYS)
        for key in keys:
            base_value = float(base_metrics[key])
            cur_value = float(cur_metrics[key])
            delta_pct = _pct_change(base_value, cur_value)
            direction = "better"
            if key in THROUGHPUT_KEYS:
                threshold_pct = abs(throughput_regression_pct)
                if threshold_overrides and backend in threshold_overrides and key in threshold_overrides[backend]:
                    threshold_pct = abs(threshold_overrides[backend][key])
                if delta_pct < 0:
                    direction = "worse"
                if delta_pct <= -threshold_pct:
                    failures.append(
                        f"{backend}:{key} regressed {delta_pct:.2f}% (threshold {-threshold_pct:.2f}%)"
                    )
            else:
                threshold_pct = abs(latency_regression_pct)
                if threshold_overrides and backend in threshold_overrides and key in threshold_overrides[backend]:
                    threshold_pct = abs(threshold_overrides[backend][key])
                if delta_pct > 0:
                    direction = "worse"
                if delta_pct >= threshold_pct:
                    failures.append(
                        f"{backend}:{key} regressed +{delta_pct:.2f}% (threshold +{threshold_pct:.2f}%)"
                    )
            lines.append(
                f"  {key}: base={base_value:.6g} current={cur_value:.6g} delta={delta_pct:+.2f}% ({direction})"
            )
        lines.append("")
    return lines, failures


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

    print(f"Baseline: {args.baseline}")
    print(f"Current : {args.current}")
    print()
    lines, failures = compare_payloads(
        baseline,
        current,
        throughput_regression_pct=args.throughput_regression_pct,
        latency_regression_pct=args.latency_regression_pct,
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
