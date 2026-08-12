from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .query import QueryEngine
from .record import PrimitiveType, Record
from .storage import RecordStore
from .verifier import RuleResult, RuleStatus, Verifier


@dataclass(frozen=True)
class MutationCaseResult:
    mutant: str
    killed: bool
    details: str


@dataclass(frozen=True)
class MutationSummary:
    total: int
    killed: int
    survived: int
    results: list[MutationCaseResult]


def run_mutation_checks() -> MutationSummary:
    cases: list[tuple[str, Callable[[], bool]]] = [
        ("immutability_bypass", _kill_immutability_bypass),
        ("signature_bypass", _kill_signature_bypass),
        ("payload_shape_bypass", _kill_payload_shape_bypass),
        ("authorization_bypass", _kill_authorization_bypass),
        ("query_mutation", _kill_query_mutation_mutant),
    ]
    results: list[MutationCaseResult] = []
    for name, runner in cases:
        try:
            killed = runner()
            details = "killed" if killed else "survived"
        except Exception as exc:
            killed = False
            details = f"error: {exc}"
        results.append(MutationCaseResult(mutant=name, killed=killed, details=details))
    killed_count = sum(1 for r in results if r.killed)
    total = len(results)
    return MutationSummary(total=total, killed=killed_count, survived=total - killed_count, results=results)


def _mk_record(record_id: str, primitive: PrimitiveType, *, signature: str, causes: tuple[str, ...] = (), authorization: tuple[str, ...] = ()) -> Record:
    payload = (
        {"subject": "s", "value": 1}
        if primitive == PrimitiveType.OBSERVATION
        else {"action": "a", "due_by": "2027-01-01"}
        if primitive == PrimitiveType.COMMITMENT
        else {"goal": "g", "horizon": "Q1"}
    )
    schema = (
        "trs.observation.v1"
        if primitive == PrimitiveType.OBSERVATION
        else "trs.commitment.v1"
        if primitive == PrimitiveType.COMMITMENT
        else "trs.intention.v1"
    )
    return Record(
        id=record_id,
        type=primitive,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema=schema,
        payload=payload,
        causes=causes,
        authorization=authorization,
        signature=signature,
    )


def _kill_immutability_bypass() -> bool:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    existing = _mk_record("dup", PrimitiveType.OBSERVATION, signature="sig:existing")
    store.append(existing)
    target = _mk_record("dup", PrimitiveType.OBSERVATION, signature="sig:target")

    original = Verifier.verify_immutability
    try:
        Verifier.verify_immutability = lambda self, record: RuleResult("4.1", "Immutability", RuleStatus.PASS, "mutated")
        result = verifier.verify(target)
        return result.valid  # mutant killed if this becomes true (test oracle violated)
    finally:
        Verifier.verify_immutability = original


def _kill_signature_bypass() -> bool:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    target = _mk_record("no-sig", PrimitiveType.OBSERVATION, signature="")
    original = Verifier.verify_signature
    try:
        Verifier.verify_signature = lambda self, record: RuleResult("5.2", "Signature Presence", RuleStatus.PASS, "mutated")
        result = verifier.verify(target)
        return result.valid
    finally:
        Verifier.verify_signature = original


def _kill_payload_shape_bypass() -> bool:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    target = Record(
        id="bad-payload",
        type=PrimitiveType.OBSERVATION,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"action": "wrong", "due_by": "2027-01-01"},
        signature="sig:bad-payload",
    )
    original = Verifier.verify_payload_shape
    try:
        Verifier.verify_payload_shape = lambda self, record: RuleResult("5.3", "Payload Shape", RuleStatus.PASS, "mutated")
        result = verifier.verify(target)
        return result.valid
    finally:
        Verifier.verify_payload_shape = original


def _kill_authorization_bypass() -> bool:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    target = _mk_record(
        "bad-auth",
        PrimitiveType.COMMITMENT,
        signature="sig:bad-auth",
        authorization=("ghost",),
    )
    original = Verifier.verify_authorization
    try:
        Verifier.verify_authorization = lambda self, record: (
            RuleResult("6.1", "Authorization Traceability", RuleStatus.PASS, "mutated"),
            ["ghost"],
        )
        result = verifier.verify(target)
        return result.valid
    finally:
        Verifier.verify_authorization = original


def _kill_query_mutation_mutant() -> bool:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    g = _mk_record("g0", PrimitiveType.OBSERVATION, signature="sig:g0")
    store.append(g)
    q = QueryEngine(store)
    original = QueryEngine.query

    def _mutated_query(self, expression):
        # Mutant: hidden write during read.
        if not self.store.exists("q-mutant"):
            rec = _mk_record("q-mutant", PrimitiveType.OBSERVATION, signature="sig:q-mutant")
            self.store.append(rec)
        return original(self, expression)

    try:
        QueryEngine.query = _mutated_query
        before = len(store.all())
        _ = q.query({"author": "alice"})
        after = len(store.all())
        return after != before
    finally:
        QueryEngine.query = original
