from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    store, verifier = make_store_and_verifier(with_genesis=False)
    cycle_attempt = Record(
        id="self-cycle",
        type=PrimitiveType.INTENTION,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.intention.v1",
        payload={"goal": "self-reference", "horizon": "Q1"},
        causes=("self-cycle",),
        signature="sig:self-cycle",
    )
    result = verifier.verify(cycle_attempt)
    blocked = (not result.valid) and any("missing causes" in err for err in result.errors)
    return blocked, f"errors={result.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_003_cycle_creation:", "BLOCKED" if ok else "VULNERABLE", detail)
