from __future__ import annotations

from dataclasses import dataclass

from .model import CheckResult, canonical_record_hash, validate_shape


@dataclass(frozen=True)
class ImportResult:
    imported_records: list[dict[str, object]]
    rejected_ids: list[str]
    shape_errors: dict[str, list[str]]
    dependency_errors: dict[str, list[str]]
    inventory: dict[str, str]
    conflict_visible: bool
    unresolved_intentions: list[str]


class IndependentInteropEngine:
    def import_unordered(self, records: list[dict[str, object]]) -> ImportResult:
        pending = [record.copy() for record in records]
        imported: dict[str, dict[str, object]] = {}
        rejected_ids: list[str] = []
        shape_errors: dict[str, list[str]] = {}
        dependency_errors: dict[str, list[str]] = {}

        while pending:
            progressed = False
            next_pending: list[dict[str, object]] = []
            for record in pending:
                record_id = str(record.get("id", ""))
                shape = validate_shape(record)
                if not shape.valid:
                    rejected_ids.append(record_id)
                    shape_errors[record_id] = shape.errors
                    continue
                dep = self._dependency_check(record, imported)
                if not dep.valid:
                    next_pending.append(record)
                    dependency_errors[record_id] = dep.errors
                    continue
                imported[record_id] = record
                progressed = True
            if not progressed:
                for record in next_pending:
                    rid = str(record.get("id", ""))
                    rejected_ids.append(rid)
                break
            pending = next_pending

        inventory = {record_id: canonical_record_hash(record) for record_id, record in imported.items()}
        unresolved = self._unresolved_intentions(list(imported.values()))
        conflict_visible = self._has_subject_scoped_conflict(list(imported.values()))
        return ImportResult(
            imported_records=sorted(imported.values(), key=lambda item: str(item.get("id"))),
            rejected_ids=sorted(set(rejected_ids)),
            shape_errors=shape_errors,
            dependency_errors=dependency_errors,
            inventory=inventory,
            conflict_visible=conflict_visible,
            unresolved_intentions=sorted(unresolved),
        )

    def _dependency_check(self, record: dict[str, object], imported: dict[str, dict[str, object]]) -> CheckResult:
        causes = [str(value) for value in record.get("causes", [])]
        authorization = [str(value) for value in record.get("authorization", [])]
        missing_causes = [record_id for record_id in causes if record_id and record_id not in imported]
        missing_auth = [record_id for record_id in authorization if record_id and record_id not in imported]
        errors: list[str] = []
        if missing_causes:
            errors.append(f"missing causes: {', '.join(missing_causes)}")
        if missing_auth:
            errors.append(f"missing authorization: {', '.join(missing_auth)}")
        if errors:
            return CheckResult(False, errors)
        return CheckResult(True, [])

    def _unresolved_intentions(self, records: list[dict[str, object]]) -> list[str]:
        intention_ids = {str(record["id"]) for record in records if record.get("type") == "Intention"}
        closed: set[str] = set()
        for record in records:
            if record.get("type") != "Observation":
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            if payload.get("subject") != "intention-closure":
                continue
            value = payload.get("value")
            if not isinstance(value, dict):
                continue
            intention_id = value.get("intention_id")
            status = value.get("status")
            if isinstance(intention_id, str) and status == "completed":
                closed.add(intention_id)
        return sorted(intention_ids - closed)

    def _has_subject_scoped_conflict(self, records: list[dict[str, object]]) -> bool:
        children_by_cause: dict[str, list[dict[str, object]]] = {}
        for record in records:
            for cause in record.get("causes", []):
                cause_id = str(cause)
                children_by_cause.setdefault(cause_id, []).append(record)
        for siblings in children_by_cause.values():
            for i in range(len(siblings)):
                left = siblings[i]
                for j in range(i + 1, len(siblings)):
                    right = siblings[j]
                    if left.get("type") != right.get("type"):
                        continue
                    if left.get("subject") != right.get("subject"):
                        continue
                    if left.get("payload") != right.get("payload"):
                        return True
        return False

