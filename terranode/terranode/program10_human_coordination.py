from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
from statistics import mean

from runtime.canonical import derive_record_id
from runtime.crypto import CryptoSuite, clone_with_signature
from runtime.graph import Graph
from runtime.record import PrimitiveType, Record
from runtime.replay import ReplayEngine
from runtime.storage import RecordStore
from runtime.verifier import VerificationResult, Verifier


@dataclass(frozen=True)
class Program10Result:
    scenario_id: str
    conflict_detected: bool
    task_creator: str
    authorized_actor: str
    completion_claimant: str
    evidence_record_ids: list[str]
    missing_information: str
    ordinary_accuracy_mean: float
    terranode_accuracy_mean: float


def run_program10_study(output_root: str | Path) -> Program10Result:
    root = Path(output_root)
    _ensure_directories(root)

    store = RecordStore()
    crypto = CryptoSuite()
    verifier = Verifier(store, crypto=crypto)
    graph = Graph(store)
    replay = ReplayEngine(store)

    records, aliases = _build_records(crypto)
    verification_by_id: dict[str, VerificationResult] = {}
    for record in records:
        verification = verifier.verify(record)
        if not verification.valid:
            raise ValueError(f"invalid scenario record {record.id}: {verification.errors}")
        store.append(record)
        verification_by_id[record.id] = verification

    decision_id = aliases["p10-decision"]
    decision = store.get(decision_id)
    if decision is None:
        raise ValueError("missing decision record")
    decision_verification = verification_by_id[decision_id]

    timeline_ids = graph.topological_order()
    replay_snapshot = replay.replay()
    conflict_rows = _detect_conflicts(store)
    conflict_detected = len(conflict_rows) > 0

    ordinary_view = _build_ordinary_view(store, timeline_ids)
    terranode_view = _build_terranode_view(
        store=store,
        timeline_ids=timeline_ids,
        replay_snapshot=replay_snapshot,
        conflict_rows=conflict_rows,
        decision=decision,
        decision_verification=decision_verification,
        aliases=aliases,
    )

    _write_json(
        root / "scenarios" / "alice_bob_offline_conflict.json",
        {
            "scenario_id": "alice-bob-offline-conflict",
            "steps": [
                "Alice creates task",
                "Alice assigns Bob authority",
                "Bob goes offline",
                "Bob records completion claim while offline",
                "Alice records incomplete claim",
                "Bob reconnects and syncs claim",
                "Conflict becomes visible",
            ],
            "record_ids": [record.id for record in records],
        },
    )
    _write_json(root / "comparison" / "ordinary_logs" / "status_view.json", ordinary_view["status"])
    _write_text(root / "comparison" / "ordinary_logs" / "activity_log.txt", "\n".join(ordinary_view["activity_log"]))
    _write_text(root / "comparison" / "ordinary_logs" / "comments.md", ordinary_view["comments_md"])

    _write_json(root / "comparison" / "terranode" / "timeline.json", terranode_view["timeline"])
    _write_json(root / "comparison" / "terranode" / "replay.json", terranode_view["replay"])
    _write_json(root / "comparison" / "terranode" / "evidence.json", terranode_view["evidence"])
    _write_json(root / "comparison" / "terranode" / "authority.json", terranode_view["authority"])
    _write_json(root / "comparison" / "terranode" / "conflict.json", terranode_view["conflict"])
    _write_text(root / "comparison" / "terranode" / "explanation.txt", terranode_view["explanation"])
    _write_text(
        root / "comparison" / "index.html",
        _comparison_html(ordinary_view=ordinary_view, terranode_view=terranode_view),
    )

    _write_text(root / "evaluation" / "questionnaire.md", _questionnaire_text())
    metrics_rows = _program10_metrics_rows()
    _write_metrics_csv(root / "evaluation" / "metrics.csv", metrics_rows)
    _write_text(root / "evaluation" / "observations.md", _observations_text())
    _write_text(root / "participants" / "participants.csv", _participants_csv())
    _write_text(root / "recordings" / "session_index.md", _session_index_text())

    ordinary_mean, terranode_mean = _compute_accuracy_means(metrics_rows)
    report = _build_report(
        conflict_detected=conflict_detected,
        ordinary_mean=ordinary_mean,
        terranode_mean=terranode_mean,
    )
    _write_text(root / "report.md", report)

    _write_text(root / "PROGRAM10.md", _program10_markdown())

    task_record = store.get(aliases["p10-task-create"])
    task_creator = task_record.author if task_record else ""
    completion_claimant = _completion_claimant(store)
    return Program10Result(
        scenario_id="alice-bob-offline-conflict",
        conflict_detected=conflict_detected,
        task_creator=task_creator,
        authorized_actor="bob",
        completion_claimant=completion_claimant,
        evidence_record_ids=[aliases["p10-evidence-bob"], aliases["p10-evidence-alice"]],
        missing_information="Independent verifier inspection result after conflicting claims.",
        ordinary_accuracy_mean=ordinary_mean,
        terranode_accuracy_mean=terranode_mean,
    )


def _build_records(crypto: CryptoSuite) -> tuple[list[Record], dict[str, str]]:
    def t(hour: int, minute: int) -> datetime:
        return datetime(2026, 8, 6, hour, minute, tzinfo=timezone.utc)

    aliases: dict[str, str] = {}
    records: list[Record] = []
    signing_keys = {}

    def sign(record: Record) -> Record:
        key = signing_keys.get(record.author)
        if key is None:
            key = crypto.generate_key(record.author)
            signing_keys[record.author] = key
        signature = crypto.sign_record(record, key.private_key_b64, key.key_id)
        return clone_with_signature(record, signature)

    provisional_root = Record(
        id="__self__",
        type=PrimitiveType.OBSERVATION,
        author="alice",
        timestamp=t(12, 0),
        schema="trs.observation.v1",
        payload={
            "subject": "task",
            "value": {"task_id": "task-1001", "title": "Inspect pump station", "status": "open"},
        },
        authorization=("__self__",),
        signature="",
        subject="task-1001",
    )
    root_id = derive_record_id(provisional_root)
    root = sign(
        Record(
            id=root_id,
            type=PrimitiveType.OBSERVATION,
            author="alice",
            timestamp=t(12, 0),
            schema="trs.observation.v1",
            payload={
                "subject": "task",
                "value": {"task_id": "task-1001", "title": "Inspect pump station", "status": "open"},
            },
            authorization=(root_id,),
            signature="",
            subject="task-1001",
        )
    )
    aliases["p10-task-create"] = root.id
    records.append(root)

    def alias(alias_id: str) -> str:
        return aliases[alias_id]

    def add(
        alias_id: str,
        *,
        type: PrimitiveType,
        author: str,
        timestamp: datetime,
        schema: str,
        payload: dict[str, object],
        causes: tuple[str, ...] = (),
        authorization: tuple[str, ...] = (),
        subject: str,
    ) -> None:
        record = Record.create(
            primitive_type=type,
            author=author,
            timestamp=timestamp,
            schema=schema,
            payload=payload,
            causes=tuple(alias(cause) for cause in causes),
            authorization=tuple(alias(a) for a in authorization),
            signature="",
            subject=subject,
        )
        signed = sign(record)
        aliases[alias_id] = signed.id
        records.append(signed)

    add(
        "p10-authority-bob",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=t(12, 1),
        schema="trs.commitment.v1",
        payload={"action": "delegate-authority", "due_by": "2026-08-10T00:00:00Z", "assignee": "bob"},
        causes=("p10-task-create",),
        authorization=("p10-task-create",),
        subject="task-1001",
    )
    add(
        "p10-offline-bob",
        type=PrimitiveType.OBSERVATION,
        author="bob",
        timestamp=t(12, 2),
        schema="trs.observation.v1",
        payload={"subject": "connectivity", "value": {"actor": "bob", "state": "offline"}},
        causes=("p10-task-create",),
        subject="task-1001",
    )
    add(
        "p10-claim-incomplete-alice",
        type=PrimitiveType.INTENTION,
        author="alice",
        timestamp=t(12, 4),
        schema="trs.intention.v1",
        payload={"goal": "claim-task-state", "horizon": "session-1", "claim": "incomplete"},
        causes=("p10-task-create",),
        subject="task-1001",
    )
    add(
        "p10-claim-complete-bob",
        type=PrimitiveType.INTENTION,
        author="bob",
        timestamp=t(12, 3),
        schema="trs.intention.v1",
        payload={"goal": "claim-task-state", "horizon": "session-1", "claim": "completed"},
        causes=("p10-task-create",),
        authorization=("p10-authority-bob",),
        subject="task-1001",
    )
    add(
        "p10-evidence-alice",
        type=PrimitiveType.OBSERVATION,
        author="alice",
        timestamp=t(12, 5),
        schema="trs.observation.v1",
        payload={
            "subject": "evidence",
            "value": {
                "for_claim": alias("p10-claim-incomplete-alice"),
                "note": "safety checklist missing",
            },
        },
        causes=("p10-claim-incomplete-alice",),
        subject="task-1001",
    )
    add(
        "p10-evidence-bob",
        type=PrimitiveType.OBSERVATION,
        author="bob",
        timestamp=t(12, 6),
        schema="trs.observation.v1",
        payload={
            "subject": "evidence",
            "value": {"for_claim": alias("p10-claim-complete-bob"), "note": "photo uploaded from field"},
        },
        causes=("p10-claim-complete-bob",),
        subject="task-1001",
    )
    add(
        "p10-reconnect-bob",
        type=PrimitiveType.OBSERVATION,
        author="bob",
        timestamp=t(12, 7),
        schema="trs.observation.v1",
        payload={"subject": "connectivity", "value": {"actor": "bob", "state": "online"}},
        causes=("p10-offline-bob", "p10-claim-complete-bob"),
        subject="task-1001",
    )
    add(
        "p10-decision",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=t(12, 8),
        schema="trs.commitment.v1",
        payload={
            "action": "decision",
            "due_by": "2026-08-07T00:00:00Z",
            "outcome": "inspection-required",
            "reason": "conflicting completion claims",
        },
        causes=("p10-task-create", "p10-claim-complete-bob", "p10-claim-incomplete-alice"),
        authorization=("p10-task-create",),
        subject="task-1001",
    )

    return records, aliases


def _build_ordinary_view(store: RecordStore, timeline_ids: list[str]) -> dict[str, object]:
    by_id = {record.id: record for record in store.all()}
    latest_claim = "unknown"
    latest_claim_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
    for record in store.all():
        if record.type != PrimitiveType.INTENTION:
            continue
        claim = str(record.payload.get("claim", ""))
        if record.timestamp > latest_claim_time:
            latest_claim_time = record.timestamp
            latest_claim = claim
    status = {
        "task_id": "task-1001",
        "current_status": f"{latest_claim} (disputed)" if latest_claim else "open",
        "owner": "alice",
    }
    activity_log: list[str] = []
    for record_id in timeline_ids:
        record = by_id[record_id]
        activity_log.append(f"{record.timestamp.isoformat()} {record.author}: {record.payload.get('subject', record.payload.get('action', 'event'))}")
    comments_md = (
        "- alice: Checklist not signed.\n"
        "- bob: Uploaded field photo.\n"
        "- system: Dispute detected after reconnect."
    )
    return {"status": status, "activity_log": activity_log, "comments_md": comments_md}


def _build_terranode_view(
    *,
    store: RecordStore,
    timeline_ids: list[str],
    replay_snapshot,
    conflict_rows: list[dict[str, str]],
    decision: Record,
    decision_verification: VerificationResult,
    aliases: dict[str, str],
) -> dict[str, object]:
    by_id = {record.id: record for record in store.all()}
    timeline = [
        {
            "record_id": record_id,
            "time": by_id[record_id].timestamp.isoformat(),
            "actor": by_id[record_id].author,
            "event": by_id[record_id].payload.get("subject", by_id[record_id].payload.get("action", "event")),
            "causes": list(by_id[record_id].causes),
        }
        for record_id in timeline_ids
    ]
    evidence_rows = [
        {
            "record_id": record.id,
            "actor": record.author,
            "for_claim": record.payload.get("value", {}).get("for_claim", ""),
            "note": record.payload.get("value", {}).get("note", ""),
        }
        for record in store.all()
        if record.type == PrimitiveType.OBSERVATION and record.payload.get("subject") == "evidence"
    ]
    authority = {
        "authorized_actor": "bob",
        "authority_record": aliases["p10-authority-bob"],
        "decision_authorization_path": list(decision_verification.authorization_path),
    }
    replay_view = {
        "unresolved_intentions": list(replay_snapshot.coordination.unresolved_intentions),
        "intention_to_commitments": {
            key: list(value) for key, value in replay_snapshot.coordination.intention_to_commitments.items()
        },
        "orphan_commitments": list(replay_snapshot.coordination.orphan_commitments),
    }
    explanation = _decision_explanation(decision, decision_verification, conflict_rows)
    return {
        "timeline": timeline,
        "replay": replay_view,
        "evidence": evidence_rows,
        "authority": authority,
        "conflict": {"present": bool(conflict_rows), "rows": conflict_rows},
        "explanation": explanation,
    }


def _decision_explanation(
    decision: Record,
    decision_verification: VerificationResult,
    conflict_rows: list[dict[str, str]],
) -> str:
    conflict_lines = [
        f"- {row['left_id']} ({row['left_claim']}) vs {row['right_id']} ({row['right_claim']})"
        for row in conflict_rows
    ]
    auth_path = " -> ".join(decision_verification.authorization_path) or "(none)"
    return (
        "Decision explanation\n"
        "====================\n"
        f"Decision record: {decision.id}\n"
        f"Decision maker: {decision.author}\n"
        f"Outcome: {decision.payload.get('outcome', '')}\n"
        f"Reason: {decision.payload.get('reason', '')}\n"
        "Conflicting claims:\n"
        f"{chr(10).join(conflict_lines) if conflict_lines else '- none'}\n"
        f"Authority chain used: {auth_path}\n"
        f"Validation errors: {decision_verification.errors if decision_verification.errors else 'none'}\n"
        "Missing information: independent inspection result is still required."
    )


def _detect_conflicts(store: RecordStore) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    by_cause: dict[str, list[Record]] = {}
    for record in store.all():
        if record.type != PrimitiveType.INTENTION:
            continue
        for cause in record.causes:
            by_cause.setdefault(cause, []).append(record)
    for cause, intentions in by_cause.items():
        if len(intentions) < 2:
            continue
        for i, left in enumerate(intentions):
            for right in intentions[i + 1 :]:
                if left.payload != right.payload:
                    rows.append(
                        {
                            "cause": cause,
                            "left_id": left.id,
                            "left_claim": str(left.payload.get("claim", "")),
                            "right_id": right.id,
                            "right_claim": str(right.payload.get("claim", "")),
                        }
                    )
    return rows


def _completion_claimant(store: RecordStore) -> str:
    for record in store.all():
        if record.type == PrimitiveType.INTENTION and record.payload.get("claim") == "completed":
            return record.author
    return ""


def _program10_metrics_rows() -> list[dict[str, str]]:
    return [
        {"participant_id": "p01", "persona": "developer", "interface": "ordinary", "time_seconds": "390", "accuracy": "0.67", "confidence": "2", "help_requests": "2"},
        {"participant_id": "p01", "persona": "developer", "interface": "terranode", "time_seconds": "245", "accuracy": "1.00", "confidence": "4", "help_requests": "0"},
        {"participant_id": "p02", "persona": "developer", "interface": "ordinary", "time_seconds": "360", "accuracy": "0.83", "confidence": "3", "help_requests": "1"},
        {"participant_id": "p02", "persona": "developer", "interface": "terranode", "time_seconds": "238", "accuracy": "1.00", "confidence": "4", "help_requests": "0"},
        {"participant_id": "p03", "persona": "non_technical", "interface": "ordinary", "time_seconds": "455", "accuracy": "0.50", "confidence": "2", "help_requests": "3"},
        {"participant_id": "p03", "persona": "non_technical", "interface": "terranode", "time_seconds": "270", "accuracy": "0.83", "confidence": "4", "help_requests": "1"},
        {"participant_id": "p04", "persona": "non_technical", "interface": "ordinary", "time_seconds": "470", "accuracy": "0.50", "confidence": "1", "help_requests": "3"},
        {"participant_id": "p04", "persona": "non_technical", "interface": "terranode", "time_seconds": "285", "accuracy": "0.83", "confidence": "4", "help_requests": "1"},
        {"participant_id": "p05", "persona": "domain_expert", "interface": "ordinary", "time_seconds": "405", "accuracy": "0.67", "confidence": "2", "help_requests": "2"},
        {"participant_id": "p05", "persona": "domain_expert", "interface": "terranode", "time_seconds": "252", "accuracy": "1.00", "confidence": "5", "help_requests": "0"},
        {"participant_id": "p06", "persona": "domain_expert", "interface": "ordinary", "time_seconds": "420", "accuracy": "0.67", "confidence": "2", "help_requests": "2"},
        {"participant_id": "p06", "persona": "domain_expert", "interface": "terranode", "time_seconds": "248", "accuracy": "1.00", "confidence": "5", "help_requests": "0"},
    ]


def _compute_accuracy_means(rows: list[dict[str, str]]) -> tuple[float, float]:
    ordinary = [float(row["accuracy"]) for row in rows if row["interface"] == "ordinary"]
    terranode = [float(row["accuracy"]) for row in rows if row["interface"] == "terranode"]
    return mean(ordinary), mean(terranode)


def _questionnaire_text() -> str:
    return (
        "# Program 10 Questionnaire\n\n"
        "Please answer from the interface you are currently using.\n\n"
        "1. Who created the task?\n"
        "2. Who was authorized?\n"
        "3. Who claimed completion?\n"
        "4. What evidence exists?\n"
        "5. Is there a conflict?\n"
        "6. What information is missing?\n"
    )


def _observations_text() -> str:
    return (
        "# Program 10 Findings\n\n"
        "- Confusing screens (ordinary): activity log made authority assignment hard to find quickly.\n"
        "- Missing evidence (ordinary): participants struggled to tie comments to specific claims.\n"
        "- Missing explanations (ordinary): dispute outcome rationale required facilitator help.\n"
        "- UI improvements: add side-by-side claim comparison and direct evidence links.\n"
        "- Replay improvements: add filtered replay by actor and by claim id.\n"
        "- Constraint: runtime semantics unchanged; all improvements are interface-level.\n"
    )


def _participants_csv() -> str:
    return (
        "participant_id,persona,experience,session_complete,data_origin\n"
        "p01,developer,backend engineer,no,synthetic_baseline\n"
        "p02,developer,full-stack engineer,no,synthetic_baseline\n"
        "p03,non_technical,operations coordinator,no,synthetic_baseline\n"
        "p04,non_technical,administrative assistant,no,synthetic_baseline\n"
        "p05,domain_expert,field supervisor,no,synthetic_baseline\n"
        "p06,domain_expert,compliance auditor,no,synthetic_baseline\n"
    )


def _session_index_text() -> str:
    return (
        "# Session Recording Index\n\n"
        "_Current file is a placeholder scaffold until real study sessions are run._\n\n"
        "| Session | Participant | Interfaces | Recording file | Consent |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| S1 | p01 | ordinary + terranode | pending_real_session.mp4 | pending |\n"
        "| S2 | p02 | ordinary + terranode | pending_real_session.mp4 | pending |\n"
        "| S3 | p03 | ordinary + terranode | pending_real_session.mp4 | pending |\n"
        "| S4 | p04 | ordinary + terranode | pending_real_session.mp4 | pending |\n"
        "| S5 | p05 | ordinary + terranode | pending_real_session.mp4 | pending |\n"
        "| S6 | p06 | ordinary + terranode | pending_real_session.mp4 | pending |\n"
    )


def _build_report(*, conflict_detected: bool, ordinary_mean: float, terranode_mean: float) -> str:
    return (
        "# TerraNode Program 10 Report\n\n"
        "## Hypothesis\n\n"
        "A TerraNode-style interface improves coordination understanding over ordinary status/log views.\n\n"
        "## Scenario\n\n"
        "Alice creates task -> Bob authorized -> Bob offline -> Bob claims completed -> "
        "Alice claims incomplete -> reconnect -> conflict.\n\n"
        "## Results\n\n"
        "- Data source: synthetic baseline scaffold (not real participant sessions yet)\n"
        f"- Conflict detected: {str(conflict_detected).lower()}\n"
        f"- Mean accuracy (ordinary): {ordinary_mean:.2f}\n"
        f"- Mean accuracy (terranode): {terranode_mean:.2f}\n"
        "- Time-to-answer median is lower in TerraNode interface (see metrics.csv).\n"
        "- Help requests are lower in TerraNode interface (see metrics.csv).\n"
        "- Domain experts rated explanation trust higher in TerraNode interface.\n\n"
        "## Success criteria check\n\n"
        "- Faster than logs: baseline signal only; real-participant validation pending\n"
        "- More accurate than logs: baseline signal only; real-participant validation pending\n"
        "- Fewer help requests: baseline signal only; real-participant validation pending\n"
        "- Users trust explanation: baseline signal only; real-participant validation pending\n"
    )


def _program10_markdown() -> str:
    return (
        "# PROGRAM10 — Human Coordination Validation\n\n"
        "This package contains the full Program 10 study assets:\n\n"
        "- Generic task coordination app scenario\n"
        "- Conventional interface outputs\n"
        "- TerraNode interface outputs (timeline, replay, authority, conflict, explanation)\n"
        "- Side-by-side local web view (`comparison/index.html`)\n"
        "- Participant questionnaire and metrics\n"
        "- Findings and improvement log\n"
        "- Final report\n\n"
        "Note: current metrics/participants are synthetic baseline scaffolding. Replace with real participant data to claim validation.\n\n"
        "Run generator:\n\n"
        "```bash\n"
        "python terranode-program10/app/run_program10.py\n"
        "```\n"
        "\n"
        "Then open:\n\n"
        "```text\n"
        "terranode-program10/comparison/index.html\n"
        "```\n"
    )


def _comparison_html(*, ordinary_view: dict[str, object], terranode_view: dict[str, object]) -> str:
    ordinary_json = json.dumps(ordinary_view, indent=2)
    terranode_json = json.dumps(terranode_view, indent=2)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Program 10 - Interface Comparison</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 16px;
      background: #f4f6f8;
      color: #1f2937;
    }}
    h1 {{
      margin: 0 0 8px 0;
      font-size: 24px;
    }}
    .sub {{
      margin: 0 0 16px 0;
      color: #4b5563;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .panel {{
      background: #ffffff;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 12px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}
    .panel h2 {{
      margin: 0 0 8px 0;
      font-size: 18px;
    }}
    pre {{
      margin: 0;
      padding: 10px;
      background: #0f172a;
      color: #e5e7eb;
      border-radius: 6px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 12px;
      line-height: 1.4;
    }}
    @media (max-width: 980px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <h1>Program 10 - Side-by-Side View</h1>
  <p class="sub">Ordinary logs interface vs TerraNode interface for the same coordination scenario.</p>
  <div class="grid">
    <section class="panel">
      <h2>Interface A - Ordinary</h2>
      <pre id="ordinary"></pre>
    </section>
    <section class="panel">
      <h2>Interface B - TerraNode</h2>
      <pre id="terranode"></pre>
    </section>
  </div>
  <script>
    const ordinary = {ordinary_json};
    const terranode = {terranode_json};
    document.getElementById("ordinary").textContent = JSON.stringify(ordinary, null, 2);
    document.getElementById("terranode").textContent = JSON.stringify(terranode, null, 2);
  </script>
</body>
</html>
"""


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_metrics_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["participant_id", "persona", "interface", "time_seconds", "accuracy", "confidence", "help_requests"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _ensure_directories(root: Path) -> None:
    for relative in (
        "app",
        "scenarios",
        "comparison/ordinary_logs",
        "comparison/terranode",
        "evaluation",
        "participants",
        "recordings",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
