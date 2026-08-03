from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "evidence" / "security"
LATEST_PATH = EVIDENCE_DIR / "cycle0014_latest.json"


def _run(cmd: list[str]) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

    checks: list[dict[str, object]] = []
    checks.append(
        _run(
            [
                sys.executable,
                "-m",
                "unittest",
                "-v",
                "tests.test_crypto_phase12",
            ]
        )
    )
    checks.append(_run([sys.executable, "-m", "unittest", "-v", "tests.test_verifier"]))
    checks.append(_run([sys.executable, "attacks/run_attacks.py"]))

    all_pass = all(int(check["exit_code"]) == 0 for check in checks)
    summary = {
        "timestamp": timestamp,
        "status": "in_progress",
        "all_internal_checks_passed": all_pass,
        "checks": checks,
        "external_audit": {
            "status": "pending",
            "required": True,
            "note": "Independent external security review is required before cycle closure.",
        },
        "entry_gate_assessment": {
            "production_crypto_path": "present",
            "threat_model": "drafted",
            "audit_scope": "drafted",
        },
    }

    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0014_readiness.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary: {summary_path.relative_to(ROOT)}")
    print(f"All internal checks passed: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
