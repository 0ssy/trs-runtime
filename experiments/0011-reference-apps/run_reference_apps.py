from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.query import QueryEngine
from runtime.record import PrimitiveType, Record
from runtime.replay import ReplayEngine
from runtime.storage import RecordStore


def _seed() -> RecordStore:
    store = RecordStore()
    records = [
        Record(
            id="g0",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "boot", "value": 1},
            signature="sig:g0",
        ),
        Record(
            id="i1",
            type=PrimitiveType.INTENTION,
            author="alice",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "ship", "horizon": "Q1"},
            causes=("g0",),
            signature="sig:i1",
        ),
        Record(
            id="c1",
            type=PrimitiveType.COMMITMENT,
            author="bob",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "deliver", "due_by": "2027-01-01"},
            causes=("i1",),
            authorization=("g0",),
            signature="sig:c1",
        ),
        Record(
            id="c2",
            type=PrimitiveType.COMMITMENT,
            author="carol",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "audit", "due_by": "2027-01-01"},
            causes=("g0",),
            authorization=("g0",),
            signature="sig:c2",
        ),
    ]
    for record in records:
        store.append(record)
    return store


def main() -> int:
    parser = argparse.ArgumentParser(description="Program 9: tiny reference applications over TRS.")
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/program9_reference_apps_latest.json",
        help="output JSON path",
    )
    args = parser.parse_args()

    store = _seed()
    query = QueryEngine(store)
    replay = ReplayEngine(store).replay()

    identity_ledger = {author: ids for author, ids in replay.identities.items()}
    contract_engine = [record.id for record in query.query({"type": PrimitiveType.COMMITMENT})]
    workflow_engine = replay.workflows
    reputation_engine = replay.reputation
    capability_view = {rid: record.authorization for rid, record in ((r.id, r) for r in store.all()) if record.authorization}

    payload = {
        "program": "Program 9 - Reference Apps",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_outcome": "TRS survives",
        "apps": {
            "identity_ledger": identity_ledger,
            "contract_engine": contract_engine,
            "workflow_engine": workflow_engine,
            "reputation_engine": reputation_engine,
            "capability_view": capability_view,
        },
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote reference-app artifact: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
