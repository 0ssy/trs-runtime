from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "evidence" / "handoff"
LATEST_PATH = EVIDENCE_DIR / "pre_pilot_external_handoff_latest.json"


def _exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def _required_entries() -> dict[str, list[str]]:
    return {
        "9.5_independent_second_implementation": [
            "research/cycles/CYCLE-0012.md",
            "research/interop/README.md",
            "research/interop/run_cycle_0012_baseline.py",
            "research/interop/run_cycle_0012_cross_impl.py",
            "evidence/interop/cycle0012_latest.json",
            "evidence/interop/cycle0012_cross_latest.json",
        ],
        "9.7_production_crypto_external_audit": [
            "research/cycles/CYCLE-0014.md",
            "research/security/README.md",
            "research/security/CYCLE0014_THREAT_MODEL.md",
            "research/security/CYCLE0014_AUDIT_SCOPE.md",
            "research/security/run_cycle_0014_readiness.py",
            "evidence/security/cycle0014_latest.json",
        ],
        "9.8_amendment_governance": [
            "research/cycles/CYCLE-0015.md",
            "research/governance/README.md",
            "research/governance/TRS_GOVERNANCE_CHARTER.md",
            "research/governance/TRS_AMENDMENT_RUNBOOK.md",
            "research/governance/run_cycle_0015_governance_check.py",
            "evidence/governance/cycle0015_latest.json",
        ],
        "9.9_live_red_team": [
            "research/cycles/CYCLE-0016.md",
            "research/redteam/README.md",
            "research/redteam/CYCLE0016_CAMPAIGN_SCOPE.md",
            "research/redteam/run_cycle_0016_redteam_sim.py",
            "evidence/redteam/cycle0016_latest.json",
            "evidence/external/2026-08-03_submission/CYCLE-0002_INDEPENDENT_ATTACK_SUBMISSION_EXTERNAL.pdf",
        ],
    }


def build_pack() -> dict[str, object]:
    required = _required_entries()
    missing: dict[str, list[str]] = {}
    present: dict[str, list[str]] = {}
    for track, paths in required.items():
        present_paths = [path for path in paths if _exists(path)]
        missing_paths = [path for path in paths if not _exists(path)]
        present[track] = present_paths
        missing[track] = missing_paths

    all_clear = all(not missing_paths for missing_paths in missing.values())
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"),
        "status": "ready_for_external_execution" if all_clear else "incomplete",
        "tracks": present,
        "missing": missing,
        "all_required_artifacts_present": all_clear,
        "execution_note": "This pack prepares external teams for 9.5/9.7/9.8/9.9 execution and closure evidence.",
    }


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    pack = build_pack()
    timestamp = pack["timestamp"]
    output = EVIDENCE_DIR / f"{timestamp}_pre_pilot_external_handoff.json"
    output.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    print(f"Handoff pack: {output.relative_to(ROOT)}")
    print(f"All required artifacts present: {pack['all_required_artifacts_present']}")
    return 0 if pack["all_required_artifacts_present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
