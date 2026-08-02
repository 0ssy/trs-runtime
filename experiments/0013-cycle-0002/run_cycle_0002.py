from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


def _run(name: str, command: list[str]) -> tuple[str, int, str]:
    proc = subprocess.run(command, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return name, proc.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CYCLE-0002 Programs 5-10.")
    parser.add_argument(
        "--scale-records",
        type=int,
        nargs="+",
        default=[10_000, 100_000],
        help="record scales for Program 5",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/cycle-0002_latest.json",
        help="cycle artifact output path",
    )
    args = parser.parse_args()

    scripts = [
        (
            "Program 5 - Scale",
            [
                sys.executable,
                "experiments/0007-scale/run_scale_campaign.py",
                "--records",
                *[str(value) for value in args.scale_records],
            ],
        ),
        ("Program 6 - Byzantine", [sys.executable, "experiments/0008-byzantine/run_byzantine_campaign.py"]),
        (
            "Program 7 - Implementation Independence",
            [sys.executable, "experiments/0009-implementation-independence/run_implementation_independence.py"],
        ),
        ("Program 8 - Formalization", [sys.executable, "experiments/0010-formalization/run_formalization_checks.py"]),
        ("Program 9 - Reference Apps", [sys.executable, "experiments/0011-reference-apps/run_reference_apps.py"]),
        (
            "Program 10 - Independent Attack Packet",
            [sys.executable, "experiments/0012-independent-attack/run_independent_attack_packet.py"],
        ),
    ]

    program_results: list[dict] = []
    for name, command in scripts:
        step_name, code, output = _run(name, command)
        program_results.append(
            {
                "program": step_name,
                "exit_code": code,
                "status": "ok" if code == 0 else "failed",
                "output_tail": output[-4000:],
            }
        )

    failed = [item for item in program_results if item["exit_code"] != 0]
    payload = {
        "cycle": "CYCLE-0002",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": program_results,
        "overall_status": "failed" if failed else "ok",
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote cycle artifact: {out_path}")
    if failed:
        print("Failed programs:")
        for item in failed:
            print(f"- {item['program']}")
        return 1
    print("All cycle programs completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
