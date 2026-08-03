from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


ALLOWED_TYPES = {"Observation", "Commitment", "Intention"}
SCHEMA_BY_TYPE = {
    "Observation": "trs.observation.v1",
    "Commitment": "trs.commitment.v1",
    "Intention": "trs.intention.v1",
}


@dataclass(frozen=True)
class CheckResult:
    valid: bool
    errors: list[str]


def canonical_record_hash(record: dict[str, object]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_shape(record: dict[str, object]) -> CheckResult:
    required = (
        "id",
        "type",
        "author",
        "timestamp",
        "schema",
        "payload",
        "causes",
        "authorization",
        "signature",
        "subject",
    )
    missing = [key for key in required if key not in record]
    if missing:
        return CheckResult(False, [f"missing required fields: {', '.join(missing)}"])

    record_type = record["type"]
    if not isinstance(record_type, str) or record_type not in ALLOWED_TYPES:
        return CheckResult(False, [f"invalid type: {record_type!r}"])

    schema = record["schema"]
    if not isinstance(schema, str) or schema != SCHEMA_BY_TYPE[record_type]:
        return CheckResult(False, [f"schema mismatch for type {record_type}: {schema!r}"])

    payload = record["payload"]
    if not isinstance(payload, dict):
        return CheckResult(False, ["payload must be an object"])

    causes = record["causes"]
    authorization = record["authorization"]
    if not isinstance(causes, list):
        return CheckResult(False, ["causes must be a list"])
    if not isinstance(authorization, list):
        return CheckResult(False, ["authorization must be a list"])

    if record_type == "Observation":
        if "subject" not in payload or "value" not in payload:
            return CheckResult(False, ["observation payload missing subject/value"])
    if record_type == "Commitment":
        if "action" not in payload or "due_by" not in payload:
            return CheckResult(False, ["commitment payload missing action/due_by"])
    if record_type == "Intention":
        if "goal" not in payload or "horizon" not in payload:
            return CheckResult(False, ["intention payload missing goal/horizon"])

    return CheckResult(True, [])

