from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    store, verifier = make_store_and_verifier()
    forged_delegation = Record(
        id="d1",
        type=PrimitiveType.COMMITMENT,
        author="mallory",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "forge-delegation", "due_by": "2027-01-01"},
        authorization=("ghost-root",),
        signature="sig:d1",
    )
    d_result = verifier.verify(forged_delegation)
    if d_result.valid:
        store.append(forged_delegation)

    transitive = Record(
        id="d2",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "operate", "due_by": "2027-01-01"},
        authorization=("d1",),
        signature="sig:d2",
    )
    t_result = verifier.verify(transitive)
    blocked = (not d_result.valid) and (not t_result.valid) and any(
        "6.1 Authorization Traceability" in err for err in t_result.errors
    )
    return blocked, f"d1_errors={d_result.errors}, d2_errors={t_result.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_007_transitive_capability:", "BLOCKED" if ok else "VULNERABLE", detail)
