from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.record import PrimitiveType, Record
from runtime.storage import LMDBStorage, RecordStore, RocksDBStorage, SQLiteStorage, StorageEngine
from runtime.sync import hash_inventory
from runtime.verifier import Verifier


def _fixtures() -> list[Record]:
    g = Record(
        id="g0",
        type=PrimitiveType.OBSERVATION,
        author="root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "boot", "value": 1},
        signature="sig:g0",
    )
    i = Record(
        id="i1",
        type=PrimitiveType.INTENTION,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.intention.v1",
        payload={"goal": "ship", "horizon": "Q1"},
        causes=("g0",),
        signature="sig:i1",
    )
    c = Record(
        id="c1",
        type=PrimitiveType.COMMITMENT,
        author="bob",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "deliver", "due_by": "2027-01-01"},
        causes=("i1",),
        authorization=("g0",),
        signature="sig:c1",
    )
    return [g, i, c]


def _load_and_verify(name: str, store: StorageEngine, records: list[Record]) -> dict:
    verifier = Verifier(store)
    accepted: list[str] = []
    for record in records:
        result = verifier.verify(record)
        if result.valid:
            store.append(record)
            accepted.append(record.id)
    inventory = hash_inventory(store)
    return {
        "backend": name,
        "accepted": accepted,
        "inventory": inventory,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Program 7: implementation-independence checks.")
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/program7_implementation_independence_latest.json",
        help="output JSON path",
    )
    args = parser.parse_args()

    records = _fixtures()
    reports: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="trs-impl-ind-") as tmp:
        stores: list[tuple[str, StorageEngine]] = [
            ("in_memory", RecordStore()),
            ("sqlite", SQLiteStorage(str(Path(tmp) / "impl.db"))),
            ("lmdb", LMDBStorage(str(Path(tmp) / "lmdb"))),
            ("rocksdb", RocksDBStorage(str(Path(tmp) / "rocks"))),
        ]
        try:
            for name, store in stores:
                reports.append(_load_and_verify(name, store, records))
        finally:
            for _, store in stores:
                close = getattr(store, "close", None)
                if callable(close):
                    close()

    inventories = [json.dumps(item["inventory"], sort_keys=True) for item in reports]
    all_equal = len(set(inventories)) == 1
    overall = "TRS survives" if all_equal else "TRS refined"
    payload = {
        "program": "Program 7 - Implementation Independence",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_outcome": overall,
        "reports": reports,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote implementation-independence artifact: {out_path}")
    return 0 if all_equal else 1


if __name__ == "__main__":
    raise SystemExit(main())
