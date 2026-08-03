from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "evidence" / "formal"
LATEST_PATH = EVIDENCE_DIR / "cycle0013_latest.json"


@dataclass(frozen=True)
class ModelRecord:
    id: str
    type: str
    subject: str
    payload: dict[str, object]
    causes: tuple[str, ...]
    authorization: tuple[str, ...]


def _build_operations() -> dict[str, ModelRecord]:
    return {
        "root": ModelRecord(
            id="root",
            type="Observation",
            subject="warehouse-7",
            payload={"subject": "warehouse-7", "value": {"available": 100}},
            causes=(),
            authorization=(),
        ),
        "cap": ModelRecord(
            id="cap",
            type="Commitment",
            subject="warehouse-7",
            payload={"action": "delegate-allocation", "due_by": "2027-01-01"},
            causes=("root",),
            authorization=("root",),
        ),
        "ia": ModelRecord(
            id="ia",
            type="Intention",
            subject="warehouse-7",
            payload={"goal": "resource-allocation", "horizon": "program-1", "amount": 80},
            causes=("root",),
            authorization=(),
        ),
        "ib": ModelRecord(
            id="ib",
            type="Intention",
            subject="warehouse-7",
            payload={"goal": "resource-allocation", "horizon": "program-1", "amount": 60},
            causes=("root",),
            authorization=(),
        ),
        "ca": ModelRecord(
            id="ca",
            type="Commitment",
            subject="warehouse-7",
            payload={"action": "grant-allocation", "due_by": "2027-01-01", "claim_id": "ia", "granted": 57.14},
            causes=("root", "ia"),
            authorization=("cap",),
        ),
        "cb": ModelRecord(
            id="cb",
            type="Commitment",
            subject="warehouse-7",
            payload={"action": "grant-allocation", "due_by": "2027-01-01", "claim_id": "ib", "granted": 42.86},
            causes=("root", "ib"),
            authorization=("cap",),
        ),
        "cla": ModelRecord(
            id="cla",
            type="Observation",
            subject="warehouse-7",
            payload={"subject": "intention-closure", "value": {"intention_id": "ia", "status": "completed"}},
            causes=("ia", "ca"),
            authorization=(),
        ),
        "clb": ModelRecord(
            id="clb",
            type="Observation",
            subject="warehouse-7",
            payload={"subject": "intention-closure", "value": {"intention_id": "ib", "status": "completed"}},
            causes=("ib", "cb"),
            authorization=(),
        ),
    }


def _is_enabled(record: ModelRecord, existing_ids: set[str]) -> bool:
    for cause in record.causes:
        if cause not in existing_ids:
            return False
    for auth in record.authorization:
        if auth not in existing_ids:
            return False
    return True


def _conflict_visible(records: list[ModelRecord]) -> bool:
    siblings_by_cause: dict[str, list[ModelRecord]] = {}
    for record in records:
        for cause in record.causes:
            siblings_by_cause.setdefault(cause, []).append(record)
    for siblings in siblings_by_cause.values():
        for i, left in enumerate(siblings):
            for right in siblings[i + 1 :]:
                if left.type != right.type:
                    continue
                if left.subject != right.subject:
                    continue
                if left.payload != right.payload:
                    return True
    return False


def _unresolved_intentions(records: list[ModelRecord]) -> list[str]:
    intentions = {record.id for record in records if record.type == "Intention"}
    closed: set[str] = set()
    for record in records:
        if record.type != "Observation":
            continue
        if record.payload.get("subject") != "intention-closure":
            continue
        value = record.payload.get("value")
        if isinstance(value, dict) and value.get("status") == "completed":
            intention_id = value.get("intention_id")
            if isinstance(intention_id, str):
                closed.add(intention_id)
    return sorted(intentions - closed)


def run_model_check() -> dict[str, object]:
    operations = _build_operations()
    op_order = tuple(operations.keys())
    frontier: list[tuple[str, ...]] = [tuple()]
    visited: set[tuple[str, ...]] = set()
    terminal_states = 0
    violations: list[str] = []
    max_depth = 0

    while frontier:
        state = frontier.pop()
        if state in visited:
            continue
        visited.add(state)
        max_depth = max(max_depth, len(state))
        existing_ids = set(state)
        enabled = []
        for op in op_order:
            if op in existing_ids:
                continue
            record = operations[op]
            if _is_enabled(record, existing_ids):
                enabled.append(op)
        records = [operations[op] for op in state]

        if len(existing_ids) != len(state):
            violations.append("duplicate id encountered")
        unresolved = _unresolved_intentions(records)
        if not enabled:
            terminal_states += 1
            if unresolved:
                violations.append(f"terminal state with unresolved intentions: {','.join(unresolved)}")

        if _conflict_visible(records) is False and {"ia", "ib"}.issubset(existing_ids):
            violations.append("conflict invisibility after dual intentions")

        for op in enabled:
            frontier.append(state + (op,))

    outcome = {
        "states_explored": len(visited),
        "terminal_states": terminal_states,
        "max_depth": max_depth,
        "violations": sorted(set(violations)),
    }
    return outcome


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    result = run_model_check()
    result["timestamp"] = timestamp
    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0013_model_check.json"
    summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Summary: {summary_path.relative_to(ROOT)}")
    print(f"States explored: {result['states_explored']}")
    print(f"Violations: {len(result['violations'])}")
    return 1 if result["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
