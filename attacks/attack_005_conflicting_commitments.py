from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.graph import Graph
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    store, verifier = make_store_and_verifier()
    c1 = Record(
        id="c1",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "close-A", "due_by": "2027-01-01"},
        causes=("g1",),
        authorization=("g1",),
        signature="sig:c1",
    )
    c2 = Record(
        id="c2",
        type=PrimitiveType.COMMITMENT,
        author="bob",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "close-B", "due_by": "2027-01-01"},
        causes=("g1",),
        authorization=("g1",),
        signature="sig:c2",
    )
    r1 = verifier.verify(c1)
    if r1.valid:
        store.append(c1)
    r2 = verifier.verify(c2)
    if r2.valid:
        store.append(c2)

    children = set(Graph(store).children("g1"))
    visible = children == {"c1", "c2"}
    return visible, f"children={sorted(children)}, r2_errors={r2.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_005_conflicting_commitments:", "BLOCKED" if ok else "VULNERABLE", detail)
