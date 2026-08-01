from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    store, verifier = make_store_and_verifier()
    c1 = Record(
        id="h1",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "approve-A", "due_by": "2027-02-01"},
        causes=("g1",),
        authorization=("g1",),
        signature="sig:h1",
    )
    c2 = Record(
        id="h2",
        type=PrimitiveType.COMMITMENT,
        author="bob",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "approve-B", "due_by": "2027-02-01"},
        causes=("g1",),
        authorization=("g1",),
        signature="sig:h2",
    )
    for rec in (c1, c2):
        res = verifier.verify(rec)
        if res.valid:
            store.append(rec)
    query = QueryEngine(store)
    visible = set(r.id for r in query.query({"cause": "g1"}))
    blocked = {"h1", "h2"}.issubset(visible)
    return blocked, f"visible={sorted(visible)}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_010_hidden_conflict:", "BLOCKED" if ok else "VULNERABLE", detail)
