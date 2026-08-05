from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable


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


def _build_transitions(
    operations: dict[str, ModelRecord], log_a: frozenset[str], log_b: frozenset[str]
) -> list[tuple[str, frozenset[str], frozenset[str]]]:
    transitions: list[tuple[str, frozenset[str], frozenset[str]]] = []
    ids_a = set(log_a)
    ids_b = set(log_b)

    for op, record in operations.items():
        if op not in ids_a and _is_enabled(record, ids_a):
            transitions.append((f"append_a:{op}", frozenset(ids_a | {op}), log_b))
        if op not in ids_b and _is_enabled(record, ids_b):
            transitions.append((f"append_b:{op}", log_a, frozenset(ids_b | {op})))

    for op in sorted(ids_a - ids_b):
        record = operations[op]
        if _is_enabled(record, ids_b):
            transitions.append((f"sync_a_to_b:{op}", log_a, frozenset(ids_b | {op})))

    for op in sorted(ids_b - ids_a):
        record = operations[op]
        if _is_enabled(record, ids_a):
            transitions.append((f"sync_b_to_a:{op}", frozenset(ids_a | {op}), log_b))

    return transitions


def _log_records(operations: dict[str, ModelRecord], log_ids: frozenset[str]) -> list[ModelRecord]:
    return [operations[op] for op in sorted(log_ids)]


def _causal_closure_holds(records: Iterable[ModelRecord], log_ids: frozenset[str]) -> bool:
    known = set(log_ids)
    for record in records:
        if not set(record.causes).issubset(known):
            return False
        if not set(record.authorization).issubset(known):
            return False
    return True


def _replay_projection(records: Iterable[ModelRecord]) -> tuple[tuple[str, ...], tuple[tuple[str, float], ...]]:
    unresolved = tuple(_unresolved_intentions(list(records)))
    grants: list[tuple[str, float]] = []
    for record in records:
        if record.type != "Commitment":
            continue
        if record.payload.get("action") != "grant-allocation":
            continue
        claim_id = record.payload.get("claim_id")
        granted = record.payload.get("granted")
        if isinstance(claim_id, str) and isinstance(granted, (int, float)):
            grants.append((claim_id, float(granted)))
    return unresolved, tuple(sorted(grants))


def run_model_check() -> dict[str, object]:
    operations = _build_operations()
    frontier: list[tuple[frozenset[str], frozenset[str]]] = [(frozenset(), frozenset())]
    visited: set[tuple[frozenset[str], frozenset[str]]] = set()
    terminal_states = 0
    violations: list[str] = []
    max_depth = 0

    while frontier:
        state = frontier.pop()
        if state in visited:
            continue
        visited.add(state)
        log_a, log_b = state
        max_depth = max(max_depth, len(log_a) + len(log_b))
        records_a = _log_records(operations, log_a)
        records_b = _log_records(operations, log_b)

        if not _causal_closure_holds(records_a, log_a):
            violations.append(f"causal closure violated in node A: {sorted(log_a)}")
        if not _causal_closure_holds(records_b, log_b):
            violations.append(f"causal closure violated in node B: {sorted(log_b)}")

        if {"ia", "ib"}.issubset(log_a) and not _conflict_visible(records_a):
            violations.append(f"conflict invisibility in node A: {sorted(log_a)}")
        if {"ia", "ib"}.issubset(log_b) and not _conflict_visible(records_b):
            violations.append(f"conflict invisibility in node B: {sorted(log_b)}")

        if log_a == log_b:
            if _replay_projection(records_a) != _replay_projection(records_b):
                violations.append(f"replay mismatch at equal inventory: {sorted(log_a)}")

        transitions = _build_transitions(operations, log_a, log_b)
        if not transitions:
            terminal_states += 1
            unresolved_a = _unresolved_intentions(records_a)
            unresolved_b = _unresolved_intentions(records_b)
            if unresolved_a:
                violations.append(
                    f"terminal node A unresolved intentions ({','.join(unresolved_a)}): {sorted(log_a)}"
                )
            if unresolved_b:
                violations.append(
                    f"terminal node B unresolved intentions ({','.join(unresolved_b)}): {sorted(log_b)}"
                )
            if log_a != log_b:
                violations.append(
                    f"terminal non-converged inventories A={sorted(log_a)} B={sorted(log_b)}"
                )

        for _, next_a, next_b in transitions:
            frontier.append((next_a, next_b))

    outcome = {
        "states_explored": len(visited),
        "terminal_states": terminal_states,
        "max_depth": max_depth,
        "invariants_checked": [
            "append-only growth per node",
            "causal and authorization closure per node",
            "conflict visibility when dual intentions coexist",
            "replay equivalence for equal inventories",
            "terminal convergence under synchronization",
            "terminal closure (no unresolved intentions)",
        ],
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
