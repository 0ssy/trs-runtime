from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    _, verifier = make_store_and_verifier(with_genesis=False)
    invalid_genesis = Record(
        id="g-bad",
        type=PrimitiveType.OBSERVATION,
        author="root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "boot", "value": 1},
        signature="",
    )
    result = verifier.verify(invalid_genesis)
    blocked = (not result.valid) and any("5.2 Signature Presence" in err for err in result.errors)
    return blocked, f"errors={result.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_006_invalid_genesis:", "BLOCKED" if ok else "VULNERABLE", detail)
