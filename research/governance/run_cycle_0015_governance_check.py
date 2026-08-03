from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "evidence" / "governance"
LATEST_PATH = EVIDENCE_DIR / "cycle0015_latest.json"


REQUIRED_STATES = (
    "Proposed",
    "Under Review",
    "Evidence Verified",
    "Ratified",
    "Rejected",
    "Deferred",
)

REQUIRED_ROLES = (
    "Steward Council",
    "Spec Editor",
    "Evidence Reviewer",
    "Implementation Reviewer",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contains_all(text: str, expected: tuple[str, ...]) -> list[str]:
    return [item for item in expected if item not in text]


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

    charter = ROOT / "research" / "governance" / "TRS_GOVERNANCE_CHARTER.md"
    runbook = ROOT / "research" / "governance" / "TRS_AMENDMENT_RUNBOOK.md"
    missing_files = [str(path.relative_to(ROOT)) for path in (charter, runbook) if not path.exists()]

    errors: list[str] = []
    if missing_files:
        errors.append(f"missing governance docs: {', '.join(missing_files)}")

    charter_text = _read(charter) if charter.exists() else ""
    runbook_text = _read(runbook) if runbook.exists() else ""
    missing_states = _contains_all(charter_text, REQUIRED_STATES)
    if missing_states:
        errors.append(f"charter missing states: {', '.join(missing_states)}")
    missing_roles = _contains_all(charter_text, REQUIRED_ROLES)
    if missing_roles:
        errors.append(f"charter missing roles: {', '.join(missing_roles)}")
    if "Ratification" not in charter_text and "Ratified" not in charter_text:
        errors.append("charter missing ratification rule")
    if "Open proposal" not in runbook_text or "Publication" not in runbook_text:
        errors.append("runbook missing process phases")

    sample_decision_trace = {
        "amendment_id": "TRS-0999",
        "transitions": [
            {"state": "Proposed", "by_role": "Spec Editor"},
            {"state": "Under Review", "by_role": "Implementation Reviewer"},
            {"state": "Evidence Verified", "by_role": "Evidence Reviewer"},
            {"state": "Ratified", "by_role": "Steward Council"},
        ],
        "audit_trail_complete": True,
    }
    decision_path = EVIDENCE_DIR / f"{timestamp}_cycle0015_sample_decision_trace.json"
    decision_path.write_text(json.dumps(sample_decision_trace, indent=2), encoding="utf-8")

    summary = {
        "timestamp": timestamp,
        "status": "in_progress",
        "errors": errors,
        "governance_docs_present": not missing_files,
        "decision_trace_path": str(decision_path.relative_to(ROOT)),
        "checks_passed": not errors,
        "closure_note": "Independent multi-party adoption exercise remains required for cycle closure.",
    }
    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0015_governance_check.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary: {summary_path.relative_to(ROOT)}")
    print(f"Checks passed: {summary['checks_passed']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
