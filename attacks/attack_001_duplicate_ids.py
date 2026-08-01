from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    store, verifier = make_store_and_verifier(with_genesis=False)
    first = Record(
        id="dup",
        type=PrimitiveType.OBSERVATION,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "x", "value": 1},
        signature="sig:dup",
    )
    store.append(first)
    second = Record(
        id="dup",
        type=PrimitiveType.OBSERVATION,
        author="mallory",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "x", "value": 999},
        signature="sig:dup2",
    )
    result = verifier.verify(second)
    blocked = (not result.valid) and any("4.1 Immutability" in err for err in result.errors)
    return blocked, f"errors={result.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_001_duplicate_ids:", "BLOCKED" if ok else "VULNERABLE", detail)
