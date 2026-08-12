from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import Verifier


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_genesis(store: RecordStore) -> None:
    genesis = Record(
        id="g1",
        type=PrimitiveType.OBSERVATION,
        author="root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "boot", "value": 1},
        authorization=("g1",),
        signature="sig:g1",
    )
    store.append(genesis)


def make_store_and_verifier(with_genesis: bool = True) -> tuple[RecordStore, Verifier]:
    store = RecordStore()
    if with_genesis:
        make_genesis(store)
    return store, Verifier(store)
