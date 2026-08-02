from __future__ import annotations

import argparse
import cProfile
from datetime import datetime, timezone
import json
from pathlib import Path
import pstats
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.benchmark import run_benchmarks


def _median_metrics(samples: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted(samples[0].keys())
    result: dict[str, float] = {}
    for key in keys:
        values = [float(sample[key]) for sample in samples]
        result[key] = float(statistics.median(values))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Program 11: in-memory performance RCA")
    parser.add_argument("--records", type=int, nargs="+", default=[200, 2000, 10000])
    parser.add_argument("--runs", type=int, default=3, help="repetitions per record count")
    parser.add_argument("--profile-records", type=int, default=10000, help="records for cProfile run")
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/program11_inmemory_perf_rca_latest.json",
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    runs_payload: list[dict] = []
    for record_count in args.records:
        samples: list[dict[str, float]] = []
        for _ in range(args.runs):
            sample = run_benchmarks(records=int(record_count), backends=("in_memory",))["in_memory"]
            samples.append(sample)
        runs_payload.append(
            {
                "records": int(record_count),
                "runs": int(args.runs),
                "median_metrics": _median_metrics(samples),
                "samples": samples,
            }
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    profile_path = out_path.parent / f"{timestamp}_program11_inmemory_profile.prof"
    profile_txt = out_path.parent / f"{timestamp}_program11_inmemory_profile_top30.txt"

    profiler = cProfile.Profile()
    profiler.enable()
    run_benchmarks(records=int(args.profile_records), backends=("in_memory",))
    profiler.disable()
    profiler.dump_stats(str(profile_path))

    stats = pstats.Stats(str(profile_path))
    stats.sort_stats("cumtime")
    lines: list[str] = []
    stats.stream = _ListStream(lines)
    stats.print_stats(30)
    profile_txt.write_text("".join(lines), encoding="utf-8")

    payload = {
        "program": "Program 11 - InMemory Perf RCA",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runs": runs_payload,
        "profile_records": int(args.profile_records),
        "profile_artifacts": {
            "raw_profile": str(profile_path).replace("\\", "/"),
            "top30_report": str(profile_txt).replace("\\", "/"),
        },
        "outcome": "NEED_MORE_EVIDENCE",
        "note": "Use this artifact to isolate in_memory replay/append/memory regressions without changing TRS semantics.",
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote in-memory RCA artifact: {out_path}")
    print(f"Wrote profile artifacts: {profile_path}, {profile_txt}")
    return 0


class _ListStream:
    def __init__(self, collector: list[str]) -> None:
        self.collector = collector

    def write(self, value: str) -> None:
        self.collector.append(value)

    def flush(self) -> None:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
