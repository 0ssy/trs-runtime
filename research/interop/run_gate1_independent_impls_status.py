from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IMPL_DIR = ROOT / "trs-independent-implementations" / "implementations"
EVIDENCE_DIR = ROOT / "evidence" / "interop"
LATEST_PATH = EVIDENCE_DIR / "gate1_independent_impls_latest.json"
TARGET_COUNT = 10
REQUIRED_PACKAGE_FILES = (
    "metadata.json",
    "README.md",
    "implementation-report.md",
    "ambiguity-report.md",
    "independence-attestation.md",
)
REQUIRED_PACKAGE_DIRS = ("src", "evidence")


@dataclass(frozen=True)
class ImplementationStatus:
    implementation_id: str
    implementation_name: str
    language: str
    team: str
    conformance_status: str
    interoperability_status: str
    ambiguity_report_status: str
    independence_attestation_status: str
    package_path: str
    evidence_paths: list[str]
    missing_required_files: list[str]
    missing_required_dirs: list[str]
    missing_evidence_paths: list[str]
    blocker_reasons: list[str]
    qualifies_for_gate_count: bool


def _status_is_pass(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower() == "pass"


def _load_metadata(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_impl_name(raw: dict[str, object], folder_name: str) -> str:
    candidate = raw.get("implementation_id", raw.get("implementation_name", folder_name))
    return str(candidate)


def _status_blocker(label: str, value: str) -> str | None:
    if _status_is_pass(value):
        return None
    return f"{label} is {value}"


def _collect_implementation_statuses() -> list[ImplementationStatus]:
    if not IMPL_DIR.exists():
        return []
    statuses: list[ImplementationStatus] = []
    for folder in sorted(path for path in IMPL_DIR.iterdir() if path.is_dir()):
        metadata_path = folder / "metadata.json"
        if not metadata_path.exists():
            continue
        raw = _load_metadata(metadata_path)
        conformance_status = str(raw.get("conformance_status", "pending"))
        interoperability_status = str(raw.get("interoperability_status", "pending"))
        ambiguity_status = str(raw.get("ambiguity_report_status", "pending"))
        attestation_status = str(raw.get("independence_attestation_status", "pending"))

        missing_required_files = [
            rel for rel in REQUIRED_PACKAGE_FILES if not (folder / rel).exists()
        ]
        missing_required_dirs = [
            rel for rel in REQUIRED_PACKAGE_DIRS if not (folder / rel).is_dir()
        ]

        evidence = raw.get("evidence_paths", [])
        evidence_paths = [str(value) for value in evidence] if isinstance(evidence, list) else []
        missing_evidence_paths = [
            rel for rel in evidence_paths if not (folder / rel).exists()
        ]

        blockers: list[str] = []
        for label, value in (
            ("conformance_status", conformance_status),
            ("interoperability_status", interoperability_status),
            ("ambiguity_report_status", ambiguity_status),
            ("independence_attestation_status", attestation_status),
        ):
            blocker = _status_blocker(label, value)
            if blocker is not None:
                blockers.append(blocker)
        if missing_required_files:
            blockers.append("missing required files: " + ", ".join(missing_required_files))
        if missing_required_dirs:
            blockers.append("missing required dirs: " + ", ".join(missing_required_dirs))
        if missing_evidence_paths:
            blockers.append("missing evidence paths: " + ", ".join(missing_evidence_paths))

        qualifies = not blockers
        statuses.append(
            ImplementationStatus(
                implementation_id=str(raw.get("implementation_id", folder.name)),
                implementation_name=_resolve_impl_name(raw, folder.name),
                language=str(raw.get("language", "unknown")),
                team=str(raw.get("team", "unknown")),
                conformance_status=conformance_status,
                interoperability_status=interoperability_status,
                ambiguity_report_status=ambiguity_status,
                independence_attestation_status=attestation_status,
                package_path=str(folder.relative_to(ROOT)),
                evidence_paths=evidence_paths,
                missing_required_files=missing_required_files,
                missing_required_dirs=missing_required_dirs,
                missing_evidence_paths=missing_evidence_paths,
                blocker_reasons=blockers,
                qualifies_for_gate_count=qualifies,
            )
        )
    return statuses


def _write_status_artifact(summary: dict[str, object]) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = str(summary["timestamp"])
    output = EVIDENCE_DIR / f"{timestamp}_gate1_independent_impls_status.json"
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output


def run_status() -> dict[str, object]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    implementations = _collect_implementation_statuses()
    qualified = [item for item in implementations if item.qualifies_for_gate_count]
    blocked = [item for item in implementations if not item.qualifies_for_gate_count]
    summary = {
        "timestamp": timestamp,
        "target_count": TARGET_COUNT,
        "registered_count": len(implementations),
        "qualified_count": len(qualified),
        "blocked_count": len(blocked),
        "remaining_to_target": max(0, TARGET_COUNT - len(qualified)),
        "gate1_pass": len(qualified) >= TARGET_COUNT,
        "implementations": [asdict(item) for item in implementations],
    }
    output_path = _write_status_artifact(summary)
    summary["summary_path"] = str(output_path.relative_to(ROOT))
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def scaffold_package(implementation_id: str, implementation_name: str, language: str, team: str) -> Path:
    package_path = IMPL_DIR / implementation_id
    package_path.mkdir(parents=True, exist_ok=True)
    metadata = {
        "implementation_id": implementation_id,
        "implementation_name": implementation_name,
        "language": language,
        "team": team,
        "conformance_status": "pending",
        "interoperability_status": "pending",
        "ambiguity_report_status": "pending",
        "independence_attestation_status": "pending",
        "evidence_paths": [],
    }
    (package_path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (package_path / "implementation-report.md").write_text(
        "\n".join(
            [
                f"# {implementation_name}",
                "",
                f"- Implementation ID: {implementation_id}",
                f"- Language: {language}",
                f"- Team: {team}",
                "",
                "## Outcome summary",
                "",
                "- Conformance: pending",
                "- Interoperability: pending",
                "- Ambiguity report: pending",
                "- Independence attestation: pending",
                "",
                "## Evidence links",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return package_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate 1 independent implementations tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Generate Gate 1 status evidence artifact")

    scaffold = subparsers.add_parser("scaffold", help="Create a new implementation package scaffold")
    scaffold.add_argument("--id", required=True, help="Implementation ID (directory name)")
    scaffold.add_argument("--name", required=True, help="Implementation display name")
    scaffold.add_argument("--language", required=True, help="Implementation language")
    scaffold.add_argument("--team", required=True, help="Team or author label")

    args = parser.parse_args()
    if args.command == "status":
        summary = run_status()
        print(f"Summary: {summary['summary_path']}")
        print(f"Qualified: {summary['qualified_count']}/{summary['target_count']}")
        print(f"Blocked: {summary['blocked_count']}")
        print(f"Gate1 pass: {summary['gate1_pass']}")
        return 0

    package = scaffold_package(args.id, args.name, args.language, args.team)
    print(f"Scaffolded: {package.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
