from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
import time
import tracemalloc
from typing import Callable

from .graph import Graph
from .query import QueryEngine
from .record import PrimitiveType, Record
from .replay import ReplayEngine
from .storage import LMDBStorage, RecordStore, RocksDBStorage, SQLiteStorage, StorageEngine
from .verifier import Verifier


@dataclass(frozen=True)
class BenchmarkMetrics:
    records: int
    append_records_per_sec: float
    verify_records_per_sec: float
    graph_descendants_sec: float
    authorization_verify_sec: float
    query_latency_ms: float
    replay_sec: float
    memory_peak_mb: float
    disk_usage_bytes: int


SUPPORTED_BACKENDS = ("in_memory", "sqlite", "lmdb", "rocksdb")


def run_benchmarks(records: int = 2000, backends: tuple[str, ...] = SUPPORTED_BACKENDS) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for backend in backends:
        if backend == "in_memory":
            results[backend] = asdict(_benchmark_in_memory(records))
        elif backend in ("sqlite", "lmdb", "rocksdb"):
            results[backend] = asdict(_benchmark_persistent(records, backend))
        else:
            raise ValueError(f"unsupported backend: {backend}")
    return results


def _benchmark_in_memory(records: int) -> BenchmarkMetrics:
    store = RecordStore()
    verifier = Verifier(store)
    return _benchmark_store("in_memory", store, verifier, records, disk_path=None)


def _benchmark_persistent(records: int, backend: str) -> BenchmarkMetrics:
    with tempfile.TemporaryDirectory(prefix=f"trs-{backend}-") as tmp:
        if backend == "sqlite":
            path = str(Path(tmp) / "trs.db")
            store: StorageEngine = SQLiteStorage(path)
        elif backend == "lmdb":
            path = str(Path(tmp) / "lmdb")
            store = LMDBStorage(path)
        elif backend == "rocksdb":
            path = str(Path(tmp) / "rocksdb")
            store = RocksDBStorage(path)
        else:
            raise ValueError(f"unsupported backend: {backend}")
        verifier = Verifier(store)
        metrics = _benchmark_store(backend, store, verifier, records, disk_path=Path(tmp))
        close = getattr(store, "close", None)
        if callable(close):
            close()
        return metrics


def _benchmark_store(
    name: str, store: StorageEngine, verifier: Verifier, records: int, disk_path: Path | None
) -> BenchmarkMetrics:
    seed = _make_seed_records(records)

    t0 = time.perf_counter()
    for record in seed:
        store.append(record)
    t1 = time.perf_counter()
    append_rps = records / max(t1 - t0, 1e-9)

    verify_record = _make_verify_target(seed[0].id)
    t2 = time.perf_counter()
    for _ in range(records):
        verifier.verify(verify_record)
    t3 = time.perf_counter()
    verify_rps = records / max(t3 - t2, 1e-9)

    graph = Graph(store)
    t4 = time.perf_counter()
    _ = graph.descendants(seed[0].id)
    t5 = time.perf_counter()
    graph_sec = t5 - t4

    auth_record = _make_auth_target(seed[0].id)
    t6 = time.perf_counter()
    _ = verifier.verify(auth_record)
    t7 = time.perf_counter()
    auth_sec = t7 - t6

    query = QueryEngine(store)
    t8 = time.perf_counter()
    _ = query.query({"type": PrimitiveType.COMMITMENT})
    t9 = time.perf_counter()
    query_ms = (t9 - t8) * 1000.0

    tracemalloc.start()
    t10 = time.perf_counter()
    _ = ReplayEngine(store, workflow_view="direct", sort_workflows=False).replay()
    t11 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    replay_sec = t11 - t10
    peak_mb = peak / (1024 * 1024)

    disk_usage = _dir_size_bytes(disk_path) if disk_path else 0
    return BenchmarkMetrics(
        records=records,
        append_records_per_sec=append_rps,
        verify_records_per_sec=verify_rps,
        graph_descendants_sec=graph_sec,
        authorization_verify_sec=auth_sec,
        query_latency_ms=query_ms,
        replay_sec=replay_sec,
        memory_peak_mb=peak_mb,
        disk_usage_bytes=disk_usage,
    )


def _make_seed_records(count: int) -> list[Record]:
    records: list[Record] = []
    genesis = Record(
        id="g0",
        type=PrimitiveType.OBSERVATION,
        author="root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "boot", "value": 1},
        signature="sig:g0",
    )
    records.append(genesis)
    prev = genesis.id
    for i in range(1, count):
        if i % 3 == 0:
            rec_type = PrimitiveType.COMMITMENT
            schema = "trs.commitment.v1"
            payload = {"action": f"deliver-{i}", "due_by": "2027-01-01"}
        elif i % 3 == 1:
            rec_type = PrimitiveType.INTENTION
            schema = "trs.intention.v1"
            payload = {"goal": f"goal-{i}", "horizon": "Q1"}
        else:
            rec_type = PrimitiveType.OBSERVATION
            schema = "trs.observation.v1"
            payload = {"subject": f"s-{i}", "value": i}

        records.append(
            Record(
                id=f"r{i}",
                type=rec_type,
                author=f"user{i % 7}",
                timestamp=datetime.now(timezone.utc),
                schema=schema,
                payload=payload,
                causes=(prev,),
                authorization=("g0",) if rec_type == PrimitiveType.COMMITMENT else (),
                signature=f"sig:r{i}",
            )
        )
        prev = f"r{i}"
    return records


def _make_verify_target(cause_id: str) -> Record:
    return Record(
        id="verify-target",
        type=PrimitiveType.INTENTION,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.intention.v1",
        payload={"goal": "verify", "horizon": "Q2"},
        causes=(cause_id,),
        signature="sig:verify-target",
    )


def _make_auth_target(auth_id: str) -> Record:
    return Record(
        id="auth-target",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "authorize", "due_by": "2027-01-01"},
        authorization=(auth_id,),
        signature="sig:auth-target",
    )


def _dir_size_bytes(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for file_name in files:
            file_path = Path(root) / file_name
            total += file_path.stat().st_size
    return total
