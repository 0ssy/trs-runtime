from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    _, verifier = make_store_and_verifier()
    mismatch = Record(
        id="schema-mismatch",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"action": "ship", "due_by": "2027-01-01"},
        signature="sig:schema-mismatch",
    )
    result = verifier.verify(mismatch)
    blocked = (not result.valid) and any("5.1 Schema Declaration" in err for err in result.errors)
    return blocked, f"errors={result.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_004_schema_mismatch:", "BLOCKED" if ok else "VULNERABLE", detail)
