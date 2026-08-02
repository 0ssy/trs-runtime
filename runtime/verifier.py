from __future__ import annotations

from collections.abc import Mapping
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .crypto import CryptoSuite
from .record import PrimitiveType, Record
from .storage import StorageEngine


class RuleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    rule_name: str
    status: RuleStatus
    reason: str


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    authorization_path: list[str]
    causal_path: list[str]
    rules: list[RuleResult] = field(default_factory=list)


DEFAULT_SCHEMA_FOR_PRIMITIVE = {
    PrimitiveType.OBSERVATION: "trs.observation.v1",
    PrimitiveType.COMMITMENT: "trs.commitment.v1",
    PrimitiveType.INTENTION: "trs.intention.v1",
}

DEFAULT_PAYLOAD_VALIDATORS: dict[PrimitiveType, Callable[[Record], tuple[bool, str]]] = {
    PrimitiveType.OBSERVATION: lambda r: _require_keys(r, ("subject", "value")),
    PrimitiveType.COMMITMENT: lambda r: _require_keys(r, ("action", "due_by")),
    PrimitiveType.INTENTION: lambda r: _require_keys(r, ("goal", "horizon")),
}


def _require_keys(record: Record, keys: tuple[str, ...]) -> tuple[bool, str]:
    if not isinstance(record.payload, Mapping):
        return False, "payload must be an object"
    missing = [k for k in keys if k not in record.payload]
    if missing:
        return False, f"missing payload keys: {', '.join(missing)}"
    return True, ""


class Verifier:
    def __init__(self, store: StorageEngine, crypto: CryptoSuite | None = None) -> None:
        self.store = store
        self.crypto = crypto
        revision = getattr(self.store, "revision", None)
        children_of_type = getattr(self.store, "children_of_type", None)
        self._revision_provider: Callable[[], int] | None = revision if callable(revision) else None
        self._children_of_type_provider: Callable[[str, PrimitiveType], list[Record]] | None = (
            children_of_type if callable(children_of_type) else None
        )
        self._cache_revision: int | None = None
        self._verification_cache: dict[tuple[int, int], VerificationResult] = {}
        self._conflict_cache: dict[tuple[int, PrimitiveType, tuple[str, ...], int], tuple[str, ...]] = {}

    def verify(self, record: Record) -> VerificationResult:
        cache_revision = self._cache_revision_key()
        if cache_revision is not None:
            self._prepare_revision_caches(cache_revision)
            verification_key = (cache_revision, id(record))
            cached_verification = self._verification_cache.get(verification_key)
            if cached_verification is not None:
                return cached_verification

        rule_results: list[RuleResult] = []
        causal_path: list[str] = []
        auth_path: list[str] = []

        immutability = self.verify_immutability(record)
        rule_results.append(immutability)

        causality, causal_path = self.verify_causality(record)
        rule_results.append(causality)

        local_sufficiency = self.verify_local_sufficiency(record)
        rule_results.append(local_sufficiency)

        closure = self.verify_closure(record)
        rule_results.append(closure)

        non_silent_conflict = self.verify_non_silent_conflict(record)
        rule_results.append(non_silent_conflict)

        authorization, auth_path = self.verify_authorization(record)
        rule_results.append(authorization)

        schema = self.verify_schema(record)
        rule_results.append(schema)

        signature = self.verify_signature(record)
        rule_results.append(signature)

        payload_shape = self.verify_payload_shape(record)
        rule_results.append(payload_shape)

        errors = [
            f"{r.rule_id} {r.rule_name}: {r.reason}"
            for r in rule_results
            if r.status == RuleStatus.FAIL
        ]
        warnings = [
            f"{r.rule_id} {r.rule_name}: {r.reason}"
            for r in rule_results
            if r.status == RuleStatus.NOT_APPLICABLE
        ]
        result = VerificationResult(
            valid=not errors,
            errors=errors,
            warnings=warnings,
            authorization_path=auth_path,
            causal_path=causal_path,
            rules=rule_results,
        )
        if cache_revision is not None:
            if len(self._verification_cache) > 4096:
                self._verification_cache.clear()
            self._verification_cache[(cache_revision, id(record))] = result
        return result

    def verify_immutability(self, record: Record) -> RuleResult:
        if self.store.exists(record.id):
            return RuleResult(
                "4.1",
                "Immutability",
                RuleStatus.FAIL,
                f"record id already exists: {record.id}",
            )
        return RuleResult("4.1", "Immutability", RuleStatus.PASS, "append-only id is unique")

    def verify_causality(self, record: Record) -> tuple[RuleResult, list[str]]:
        if not record.causes:
            return (
                RuleResult("4.2", "Causality", RuleStatus.NOT_APPLICABLE, "genesis-like record"),
                [],
            )
        missing = [rid for rid in record.causes if not self.store.exists(rid)]
        if missing:
            return (
                RuleResult("4.2", "Causality", RuleStatus.FAIL, f"missing causes: {', '.join(missing)}"),
                [],
            )
        return (
            RuleResult("4.2", "Causality", RuleStatus.PASS, "all causes present"),
            list(record.causes),
        )

    def verify_local_sufficiency(self, record: Record) -> RuleResult:
        _ = record
        return RuleResult(
            "4.3",
            "Local Sufficiency",
            RuleStatus.PASS,
            "verification depends on local record graph only",
        )

    def verify_closure(self, record: Record) -> RuleResult:
        if record.type != PrimitiveType.INTENTION:
            return RuleResult(
                "4.4",
                "Closure",
                RuleStatus.NOT_APPLICABLE,
                "closure applies to intention records",
            )
        if not record.causes:
            return RuleResult(
                "4.4",
                "Closure",
                RuleStatus.FAIL,
                "intention must reference at least one causal record",
            )
        missing = [rid for rid in record.causes if not self.store.exists(rid)]
        if missing:
            return RuleResult("4.4", "Closure", RuleStatus.FAIL, f"missing causes: {', '.join(missing)}")
        return RuleResult("4.4", "Closure", RuleStatus.PASS, "intention is causally closed")

    def verify_non_silent_conflict(self, record: Record) -> RuleResult:
        store_revision = self._store_revision()
        if store_revision is not None:
            cache_key = (store_revision, record.type, tuple(record.causes), id(record.payload))
            cached = self._conflict_cache.get(cache_key)
            if cached is not None:
                if cached:
                    return RuleResult(
                        "4.5",
                        "Non-Silent Conflict",
                        RuleStatus.PASS,
                        f"conflict explicitly visible with siblings: {', '.join(cached)}",
                    )
                return RuleResult("4.5", "Non-Silent Conflict", RuleStatus.NOT_APPLICABLE, "no conflict detected")

        conflicting: list[str] = []
        for cause_id in record.causes:
            for sibling in self._children_of_type(cause_id, record.type):
                if sibling.subject == record.subject and sibling.payload != record.payload:
                    conflicting.append(sibling.id)
        if store_revision is not None:
            self._conflict_cache[cache_key] = tuple(conflicting)
        if conflicting:
            return RuleResult(
                "4.5",
                "Non-Silent Conflict",
                RuleStatus.PASS,
                f"conflict explicitly visible with siblings: {', '.join(conflicting)}",
            )
        return RuleResult("4.5", "Non-Silent Conflict", RuleStatus.NOT_APPLICABLE, "no conflict detected")

    def verify_authorization(self, record: Record) -> tuple[RuleResult, list[str]]:
        if not record.authorization:
            return (
                RuleResult(
                    "6.1",
                    "Authorization Traceability",
                    RuleStatus.NOT_APPLICABLE,
                    "no authorization references",
                ),
                [],
            )

        missing = [rid for rid in record.authorization if not self.store.exists(rid)]
        if missing:
            return (
                RuleResult(
                    "6.1",
                    "Authorization Traceability",
                    RuleStatus.FAIL,
                    f"missing authorization records: {', '.join(missing)}",
                ),
                [],
            )

        genesis_ids = {r.id for r in self.store.all() if not r.causes and not r.authorization}
        for auth_id in record.authorization:
            path = self._find_authorization_path(auth_id, genesis_ids)
            if path:
                if self.crypto:
                    delegation_ok, delegation_reason = self._verify_delegation_chain(record, path)
                    if not delegation_ok:
                        return (
                            RuleResult(
                                "6.1",
                                "Authorization Traceability",
                                RuleStatus.FAIL,
                                delegation_reason,
                            ),
                            [],
                        )
                return (
                    RuleResult(
                        "6.1",
                        "Authorization Traceability",
                        RuleStatus.PASS,
                        "delegation path to genesis found",
                    ),
                    path,
                )
        return (
            RuleResult(
                "6.1",
                "Authorization Traceability",
                RuleStatus.FAIL,
                "missing delegation path to genesis",
            ),
            [],
        )

    def verify_schema(self, record: Record) -> RuleResult:
        expected = DEFAULT_SCHEMA_FOR_PRIMITIVE.get(record.type)
        if expected is None:
            return RuleResult("5.1", "Schema Declaration", RuleStatus.FAIL, "unknown primitive type")
        if record.schema != expected:
            return RuleResult(
                "5.1",
                "Schema Declaration",
                RuleStatus.FAIL,
                f"schema {record.schema} does not match declared primitive {record.type.value}",
            )
        return RuleResult("5.1", "Schema Declaration", RuleStatus.PASS, "schema matches primitive")

    def verify_signature(self, record: Record) -> RuleResult:
        if not record.signature:
            return RuleResult("5.2", "Signature Presence", RuleStatus.FAIL, "missing signature")
        if self.crypto is None:
            if record.signature.startswith("sig:") or record.signature.startswith("ed25519:"):
                return RuleResult("5.2", "Signature Presence", RuleStatus.PASS, "signature present")
            return RuleResult("5.2", "Signature Presence", RuleStatus.FAIL, "signature format invalid")
        ok, reason = self.crypto.verify_record_signature(record)
        if not ok:
            return RuleResult("5.2", "Signature Presence", RuleStatus.FAIL, reason)
        return RuleResult("5.2", "Signature Presence", RuleStatus.PASS, "signature verified")

    def verify_payload_shape(self, record: Record) -> RuleResult:
        validator = DEFAULT_PAYLOAD_VALIDATORS.get(record.type)
        if validator is None:
            return RuleResult("5.3", "Payload Shape", RuleStatus.FAIL, "no validator for primitive")
        ok, reason = validator(record)
        if not ok:
            return RuleResult("5.3", "Payload Shape", RuleStatus.FAIL, reason)
        return RuleResult(
            "5.3",
            "Payload Shape",
            RuleStatus.PASS,
            f"payload valid for declared primitive {record.type.value}",
        )

    def _find_authorization_path(self, start_id: str, genesis_ids: set[str]) -> list[str]:
        queue = deque([(start_id, [start_id])])
        visited = {start_id}
        while queue:
            current_id, path = queue.popleft()
            if current_id in genesis_ids:
                return path
            current = self.store.get(current_id)
            if current is None:
                continue
            for parent in (*current.authorization, *current.causes):
                if parent not in visited and self.store.exists(parent):
                    visited.add(parent)
                    queue.append((parent, [*path, parent]))
        return []

    def _verify_delegation_chain(self, record: Record, auth_path: list[str]) -> tuple[bool, str]:
        child_author = record.author
        for auth_id in auth_path:
            parent = self.store.get(auth_id)
            if parent is None:
                return False, f"authorization record missing during delegation check: {auth_id}"
            if child_author != parent.author and not self.crypto.has_delegation(parent.author, child_author):
                return (
                    False,
                    f"missing delegation from {parent.author} to {child_author} in authorization chain",
                )
            child_author = parent.author
        return True, ""

    def _children_of_type(self, record_id: str, primitive: PrimitiveType) -> list[Record]:
        if self._children_of_type_provider is not None:
            return self._children_of_type_provider(record_id, primitive)
        return [child for child in self.store.children(record_id) if child.type == primitive]

    def _store_revision(self) -> int | None:
        if self._revision_provider is not None:
            value = self._revision_provider()
            return value if isinstance(value, int) else None
        return None

    def _cache_revision_key(self) -> int | None:
        store_revision = self._store_revision()
        if store_revision is None:
            return None
        if self.crypto is None:
            return store_revision
        crypto_revision = getattr(self.crypto, "revision", None)
        if callable(crypto_revision):
            c_rev = crypto_revision()
            if isinstance(c_rev, int):
                return (store_revision << 32) ^ c_rev
        return store_revision

    def _prepare_revision_caches(self, cache_revision: int) -> None:
        if self._cache_revision == cache_revision:
            return
        self._cache_revision = cache_revision
        self._verification_cache.clear()
        self._conflict_cache.clear()
