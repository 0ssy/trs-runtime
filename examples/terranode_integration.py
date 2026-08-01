from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.terranode_adapter import TerraNodeRuntimeAdapter


def main() -> None:
    adapter = TerraNodeRuntimeAdapter()

    genesis = {
        "id": "g1",
        "type": "Observation",
        "author": "root",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema": "trs.observation.v1",
        "payload": {"subject": "boot", "value": 1},
        "signature": "sig:g1",
    }
    genesis_result = adapter.submit_envelope(genesis)
    print("Genesis accepted:", genesis_result.accepted)
    print("Genesis errors:", genesis_result.verification.errors)

    intention = {
        "id": "i1",
        "type": "Intention",
        "author": "alice",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema": "trs.intention.v1",
        "payload": {"goal": "ship", "horizon": "Q1"},
        "causes": ["g1"],
        "signature": "sig:i1",
    }
    intention_result = adapter.submit_envelope(intention)
    print("Intention accepted:", intention_result.accepted)
    print("Intention errors:", intention_result.verification.errors)

    forged = {
        "id": "bad1",
        "type": "Observation",
        "author": "mallory",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema": "trs.observation.v1",
        "payload": {"action": "forge", "due_by": "2027-01-01"},
        "signature": "sig:bad1",
    }
    forged_result = adapter.submit_envelope(forged)
    print("Forged accepted:", forged_result.accepted)
    print("Forged errors:", forged_result.verification.errors)

    found = adapter.query({"author": "alice"})
    print("Alice records:", [record.id for record in found])

    print("Children of g1:", adapter.children("g1"))


if __name__ == "__main__":
    main()
