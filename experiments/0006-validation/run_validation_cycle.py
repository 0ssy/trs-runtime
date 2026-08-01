from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


def _run_step(name: str, command: list[str], log_path: Path) -> int:
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== {name} ===\n")
        log.write("$ " + " ".join(command) + "\n")
        proc = subprocess.run(command, capture_output=True, text=True)
        log.write(proc.stdout)
        log.write(proc.stderr)
        log.write(f"\n(exit={proc.returncode})\n")
        return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the TRS runtime validation cycle.")
    parser.add_argument("--gate-mode", choices=["quick", "dev", "pr", "ci", "nightly"], default="pr")
    parser.add_argument(
        "--allow-benchmark-regressions",
        action="store_true",
        help="Do not fail the validation cycle when only the benchmark gate fails.",
    )
    args = parser.parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    log_path = Path("evidence") / "test_runs" / f"{timestamp}_validation_cycle.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    steps: list[tuple[str, list[str]]] = [
        ("Unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]),
        ("Conformance tests", [sys.executable, "-m", "unittest", "discover", "-s", "conformance", "-p", "test_*.py"]),
        ("Attack suite", [sys.executable, "attacks/run_attacks.py"]),
        ("Mutation checks", [sys.executable, "experiments/0003-mutation/run_mutation_checks.py"]),
        (
            "Benchmark gate",
            [
                sys.executable,
                "benchmarks/gate_benchmarks.py",
                "--mode",
                args.gate_mode,
                "--baseline",
                "evidence/benchmarks/2026-08-01_phase15_baseline.json",
            ],
        ),
    ]

    failures: list[str] = []
    for name, command in steps:
        code = _run_step(name, command, log_path)
        if code != 0:
            if name == "Benchmark gate" and args.allow_benchmark_regressions:
                continue
            failures.append(name)

    print(f"Validation log: {log_path}")
    if failures:
        print("Failed steps:")
        for step in failures:
            print(f"- {step}")
        return 1
    print("All validation steps passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
