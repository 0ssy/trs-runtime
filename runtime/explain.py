from __future__ import annotations

from .record import Record
from .storage import StorageEngine
from .verifier import RuleStatus, VerificationResult


def explain(record: Record, verification: VerificationResult, store: StorageEngine) -> str:
    dependents = [r.id for r in store.children(record.id)]

    lines: list[str] = [
        f"Record: {record.id}",
        f"Primitive: {record.type.value}",
        f"Schema: {record.schema}",
        f"Authorization: {', '.join(record.authorization) if record.authorization else '(none)'}",
        f"Causality: {', '.join(record.causes) if record.causes else '(genesis-like)'}",
        f"Dependents: {', '.join(dependents) if dependents else '(none)'}",
        "Verification summary:",
    ]

    for rule in verification.rules:
        lines.append(f"- Rule {rule.rule_id} {rule.rule_name}: {rule.status.value}")
        lines.append(f"  Reason: {rule.reason}")
        if rule.status == RuleStatus.FAIL:
            lines.append("  Action: inspect this rule failure before appending record.")

    if verification.authorization_path:
        lines.append(f"Authorization path: {' -> '.join(verification.authorization_path)}")
    if verification.causal_path:
        lines.append(f"Causal path: {' -> '.join(verification.causal_path)}")

    lines.append(f"Valid: {verification.valid}")
    return "\n".join(lines)
