from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    store, verifier = make_store_and_verifier()
    forged = Record(
        id="forged-commitment",
        type=PrimitiveType.COMMITMENT,
        author="mallory",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "approve-transfer", "due_by": "2027-01-01"},
        authorization=("ghost-capability",),
        signature="sig:forged-commitment",
    )
    result = verifier.verify(forged)
    blocked = (not result.valid) and any("6.1 Authorization Traceability" in err for err in result.errors)
    return blocked, f"errors={result.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_002_forged_authority:", "BLOCKED" if ok else "VULNERABLE", detail)
