from __future__ import annotations

from datetime import datetime, timezone

from _shared import make_store_and_verifier
from runtime.record import PrimitiveType, Record


def run() -> tuple[bool, str]:
    _, verifier = make_store_and_verifier()
    sniff = Record(
        id="sniff-1",
        type=PrimitiveType.OBSERVATION,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"action": "this-looks-like-commitment", "due_by": "2027-01-01"},
        signature="sig:sniff-1",
    )
    result = verifier.verify(sniff)
    blocked = (not result.valid) and any("5.3 Payload Shape" in err for err in result.errors)
    return blocked, f"errors={result.errors}"


if __name__ == "__main__":
    ok, detail = run()
    print("attack_008_payload_sniffing:", "BLOCKED" if ok else "VULNERABLE", detail)
