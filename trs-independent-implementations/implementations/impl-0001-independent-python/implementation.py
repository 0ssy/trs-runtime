"""Independent TRS implementation derived only from the frozen spec artifacts.

This module intentionally has no imports from the repository's runtime package.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMAS = {
    "Observation": "trs.observation.v1",
    "Commitment": "trs.commitment.v1",
    "Intention": "trs.intention.v1",
}


@dataclass(frozen=True)
class Check:
    valid: bool
    errors: tuple[str, ...] = ()


class TRSError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def validate_record(record: dict[str, Any], existing: dict[str, dict[str, Any]] | None = None) -> Check:
    existing = existing or {}
    errors: list[str] = []
    required = ("id", "type", "author", "timestamp", "schema", "payload", "causes", "authorization", "signature", "subject")
    missing = [key for key in required if key not in record]
    if missing:
        return Check(False, ("5.1 Record Envelope: missing required fields: " + ", ".join(missing),))
    rid = record["id"]
    if not isinstance(rid, str) or not rid:
        errors.append("5.1 Record Envelope: id must be a non-empty string")
    if isinstance(rid, str) and rid in existing:
        errors.append("4.1 Immutability: duplicate record id")
    kind = record["type"]
    if kind not in SCHEMAS:
        errors.append(f"5.1 Record Envelope: invalid primitive type {kind!r}")
    if isinstance(kind, str) and record["schema"] != SCHEMAS.get(kind):
        errors.append(f"5.1 Schema Declaration: schema mismatch for type {kind}")
    if not isinstance(record["author"], str) or not record["author"]:
        errors.append("5.1 Record Envelope: author must be a non-empty string")
    if not isinstance(record["timestamp"], str) or not record["timestamp"]:
        errors.append("5.1 Record Envelope: timestamp must be a non-empty string")
    if not isinstance(record["signature"], str) or not record["signature"]:
        errors.append("5.1 Record Envelope: signature must be present")
    if not isinstance(record["payload"], dict):
        errors.append("5.3 Payload Shape: payload must be an object")
    if not isinstance(record["causes"], list):
        errors.append("4.2 Causality: causes must be a list")
    if not isinstance(record["authorization"], list):
        errors.append("6.1 Authorization Traceability: authorization must be a list")
    if isinstance(record["causes"], list):
        missing_causes = [str(x) for x in record["causes"] if str(x) not in existing]
        if missing_causes:
            errors.append("4.2 Causality: missing causes: " + ", ".join(missing_causes))
    if isinstance(record["authorization"], list):
        missing_auth = [str(x) for x in record["authorization"] if str(x) not in existing]
        if missing_auth:
            errors.append("6.1 Authorization Traceability: missing authorization records: " + ", ".join(missing_auth))
    if kind == "Observation" and isinstance(record["payload"], dict):
        absent = [key for key in ("subject", "value") if key not in record["payload"]]
        if absent:
            errors.append("5.3 Payload Shape: missing payload keys: " + ", ".join(absent))
    if kind == "Commitment" and isinstance(record["payload"], dict):
        absent = [key for key in ("action", "due_by") if key not in record["payload"]]
        if absent:
            errors.append("5.3 Payload Shape: missing payload keys: " + ", ".join(absent))
    if kind == "Intention" and isinstance(record["payload"], dict):
        absent = [key for key in ("goal", "horizon") if key not in record["payload"]]
        if absent:
            errors.append("5.3 Payload Shape: missing payload keys: " + ", ".join(absent))
    if kind == "Observation" and "origin" in record and record["origin"] not in ("witnessed", "inferred"):
        errors.append("6.3 Observation Origin: invalid origin")
    if errors:
        return Check(False, tuple(errors))
    return Check(True)


class TRSRuntime:
    """Append-only local graph with structural verification and policy-neutral queries."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}

    def append(self, record: dict[str, Any]) -> Check:
        candidate = deepcopy(record)
        result = validate_record(candidate, self._records)
        if result.valid:
            self._records[candidate["id"]] = candidate
        return result

    def all_records(self) -> list[dict[str, Any]]:
        return [deepcopy(self._records[key]) for key in sorted(self._records)]

    def get(self, record_id: str) -> dict[str, Any] | None:
        return deepcopy(self._records.get(record_id))

    def inventory(self) -> dict[str, str]:
        return {key: record_hash(value) for key, value in sorted(self._records.items())}

    def conflict_visible(self) -> bool:
        children: dict[str, list[dict[str, Any]]] = {}
        for record in self._records.values():
            for cause in record["causes"]:
                children.setdefault(str(cause), []).append(record)
        for siblings in children.values():
            for left_index, left in enumerate(siblings):
                for right in siblings[left_index + 1:]:
                    if left["type"] == right["type"] and left["subject"] == right["subject"] and left["payload"] != right["payload"]:
                        return True
        return False

    def replay(self) -> dict[str, Any]:
        intentions = {r["id"] for r in self._records.values() if r["type"] == "Intention"}
        closed: set[str] = set()
        for record in self._records.values():
            if record["type"] != "Observation":
                continue
            payload = record["payload"]
            if payload.get("subject") == "intention-closure" and isinstance(payload.get("value"), dict):
                value = payload["value"]
                if value.get("status") in {"completed", "cancelled", "expired"} and isinstance(value.get("intention_id"), str):
                    closed.add(value["intention_id"])
        links: dict[str, list[str]] = {}
        for record in self._records.values():
            if record["type"] != "Commitment":
                continue
            for cause in record["causes"]:
                if cause in intentions:
                    links.setdefault(cause, []).append(record["id"])
        return {"unresolved_intentions": sorted(intentions - closed), "intention_to_commitments": {k: sorted(v) for k, v in sorted(links.items())}}

    def import_unordered(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        pending = [deepcopy(r) for r in records]
        rejected: list[str] = []
        errors: dict[str, list[str]] = {}
        while pending:
            progress = False
            rest: list[dict[str, Any]] = []
            for record in pending:
                result = validate_record(record, self._records)
                if result.valid:
                    self._records[record["id"]] = record
                    progress = True
                else:
                    if any("missing causes" in e or "missing authorization records" in e for e in result.errors):
                        rest.append(record)
                        errors[record.get("id", "")] = list(result.errors)
                    else:
                        rejected.append(str(record.get("id", "")))
                        errors[str(record.get("id", ""))] = list(result.errors)
            if not progress:
                rejected.extend(str(r.get("id", "")) for r in rest)
                break
            pending = rest
        return {"imported_records": self.all_records(), "rejected_ids": sorted(set(rejected)), "errors": errors, "inventory": self.inventory(), "conflict_visible": self.conflict_visible(), **self.replay()}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
