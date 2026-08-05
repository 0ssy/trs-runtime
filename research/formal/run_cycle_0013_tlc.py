from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
FORMAL_TLA_DIR = ROOT / "trs-formal" / "tla"
EVIDENCE_DIR = ROOT / "evidence" / "formal"
TLC_EVIDENCE_DIR = EVIDENCE_DIR / "tlc"
LATEST_PATH = EVIDENCE_DIR / "cycle0013_tlc_latest.json"


@dataclass(frozen=True)
class TlcSummary:
    status: str
    states_generated: int
    distinct_states: int
    search_depth: int
    duration_seconds: int
    log_path: str
    timestamp: str
    command: list[str]


def _parse_int(pattern: str, text: str) -> int:
    match = re.search(pattern, text)
    if match is None:
        raise ValueError(f"Unable to parse pattern: {pattern}")
    return int(match.group(1))


def _parse_duration_seconds(text: str) -> int:
    match = re.search(r"Finished in (\d+)s", text)
    if match is not None:
        return int(match.group(1))
    alt = re.search(r"Finished in (\d{2})m (\d{2})s", text)
    if alt is None:
        raise ValueError("Unable to parse TLC duration")
    return int(alt.group(1)) * 60 + int(alt.group(2))


def _build_summary(output: str, log_path: Path, timestamp: str, command: list[str]) -> TlcSummary:
    status = "pass" if "Model checking completed. No error has been found." in output else "fail"
    states_generated = _parse_int(r"(\d+)\s+states generated", output)
    distinct_states = _parse_int(r"\d+\s+states generated,\s+(\d+)\s+distinct states found", output)
    search_depth = _parse_int(r"The depth of the complete state graph search is\s+(\d+)\.", output)
    duration_seconds = _parse_duration_seconds(output)
    return TlcSummary(
        status=status,
        states_generated=states_generated,
        distinct_states=distinct_states,
        search_depth=search_depth,
        duration_seconds=duration_seconds,
        log_path=str(log_path.relative_to(ROOT)),
        timestamp=timestamp,
        command=command,
    )


def _resolve_tlc_jar(cli_value: str | None) -> Path:
    if cli_value:
        jar = Path(cli_value)
    else:
        env_raw = os.environ.get("TLA2TOOLS_JAR")
        if env_raw:
            jar = Path(env_raw)
        else:
            jar = Path(os.environ["TEMP"]) / "tla2tools.jar"
    if not jar.exists():
        raise FileNotFoundError(f"TLC jar not found: {jar}")
    return jar


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TLC for CYCLE-0013 and write evidence artifacts.")
    parser.add_argument("--tlc-jar", help="Path to tla2tools.jar. Defaults to TLA2TOOLS_JAR or %TEMP%\\tla2tools.jar")
    args = parser.parse_args()

    tlc_jar = _resolve_tlc_jar(args.tlc_jar)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    TLC_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    log_path = TLC_EVIDENCE_DIR / f"{timestamp}_cycle0013_tlc.log"

    command = [
        "java",
        "-cp",
        str(tlc_jar),
        "tlc2.TLC",
        "-cleanup",
        "-deadlock",
        "-config",
        "TrsCore.cfg",
        "TrsCore.tla",
    ]
    proc = subprocess.run(
        command,
        cwd=FORMAL_TLA_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = proc.stdout + proc.stderr
    log_path.write_text(output, encoding="utf-8")
    summary = _build_summary(output, log_path, timestamp, command)

    summary_json = {
        "status": summary.status,
        "states_generated": summary.states_generated,
        "distinct_states": summary.distinct_states,
        "search_depth": summary.search_depth,
        "duration_seconds": summary.duration_seconds,
        "log_path": summary.log_path,
        "timestamp": summary.timestamp,
        "command": summary.command,
    }
    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0013_tlc.json"
    summary_path.write_text(json.dumps(summary_json, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary_json, indent=2), encoding="utf-8")

    print(f"Summary: {summary_path.relative_to(ROOT)}")
    print(f"Log: {log_path.relative_to(ROOT)}")
    print(f"Status: {summary.status}")
    return 0 if summary.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
