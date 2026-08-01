from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    store, verifier = make_store_and_verifier()
    rec = Record(
        id="i1",
        type=PrimitiveType.INTENTION,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.intention.v1",
        payload={"goal": "ship", "horizon": "Q1"},
        causes=("g1",),
        signature="sig:i1",
    )
    r = verifier.verify(rec)
    if r.valid:
        store.append(rec)
    query = QueryEngine(store)
    before = len(store.all())
    _ = query.query({"author": "alice"})
    after = len(store.all())
    blocked = before == after
    return blocked, f"before={before}, after={after}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_009_query_mutation:", "BLOCKED" if ok else "VULNERABLE", detail)
