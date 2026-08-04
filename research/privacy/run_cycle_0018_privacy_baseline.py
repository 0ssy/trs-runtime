from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "evidence" / "privacy"
LATEST_PATH = EVIDENCE_DIR / "cycle0018_latest.json"


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

    cmd = [sys.executable, "-m", "unittest", "-v", "terranode.tests.test_program9_11_privacy"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    summary = {
        "timestamp": timestamp,
        "status": "in_progress",
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "privacy_baseline_passed": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "initial_claims": ["membership", "age_over_18", "allocation_tier"],
        "closure_note": "ZK/VC-grade proof systems and external privacy review remain required.",
    }
    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0018_privacy_baseline.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary: {summary_path.relative_to(ROOT)}")
    print(f"Privacy baseline passed: {summary['privacy_baseline_passed']}")
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
