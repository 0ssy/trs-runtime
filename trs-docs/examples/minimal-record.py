from __future__ import annotations

from datetime import datetime, timezone


record = {
    "id": "g1",
    "type": "Observation",
    "author": "root",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "schema": "trs.observation.v1",
    "payload": {"subject": "boot", "value": 1},
    "causes": [],
    "authorization": [],
    "signature": "sig:g1",
}

print(record)

