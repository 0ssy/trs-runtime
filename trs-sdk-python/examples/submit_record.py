from __future__ import annotations

from datetime import datetime, timezone

from trs import Client


def main() -> None:
    client = Client("http://localhost:8080")
    record = {
        "id": "g1",
        "type": "Observation",
        "author": "demo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema": "trs.observation.v1",
        "payload": {"subject": "water", "value": 10},
        "causes": [],
        "authorization": [],
        "signature": "sig:g1",
    }
    print(client.submit(record))


if __name__ == "__main__":
    main()

