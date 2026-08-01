from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import json
import os
import sqlite3
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Protocol, Set

from .record import PrimitiveType, Record

try:
    import lmdb as _lmdb
except ImportError:  # pragma: no cover
    _lmdb = None

try:
    from rocksdict import Rdict as _Rdict
except ImportError:  # pragma: no cover
    _Rdict = None


class StorageEngine(Protocol):
    def append(self, record: Record) -> None: ...
    def get(self, record_id: str) -> Record | None: ...
    def exists(self, record_id: str) -> bool: ...
    def children(self, record_id: str) -> list[Record]: ...
    def parents(self, record_id: str) -> list[str]: ...
    def all(self) -> list[Record]: ...
    def query(self, expression: Mapping[str, Any]) -> list[Record]: ...


def filter_records(records: Iterable[Record], expression: Mapping[str, Any]) -> list[Record]:
    current = list(records)
    for key, value in expression.items():
        if key == "type":
            primitive = value if isinstance(value, PrimitiveType) else PrimitiveType(value)
            current = [r for r in current if r.type == primitive]
        elif key == "author":
            current = [r for r in current if r.author == value]
        elif key == "schema":
            current = [r for r in current if r.schema == value]
        elif key == "cause":
            current = [r for r in current if value in r.causes]
        elif key == "authorization":
            current = [r for r in current if value in r.authorization]
        else:
            raise ValueError(f"unsupported query key: {key}")
    return current


@dataclass
class RecordStore:
    _records: Dict[str, Record] = field(default_factory=dict)
    _append_order: List[str] = field(default_factory=list)
    _children: Dict[str, Set[str]] = field(default_factory=dict)

    def append(self, record: Record) -> None:
        if record.id in self._records:
            raise ValueError(f"record already exists: {record.id}")
        self._records[record.id] = record
        self._append_order.append(record.id)
        for parent_id in record.causes:
            self._children.setdefault(parent_id, set()).add(record.id)

    def get(self, record_id: str) -> Record | None:
        return self._records.get(record_id)

    def exists(self, record_id: str) -> bool:
        return record_id in self._records

    def children(self, record_id: str) -> list[Record]:
        child_ids = self._children.get(record_id, set())
        return [self._records[rid] for rid in self._append_order if rid in child_ids]

    def parents(self, record_id: str) -> list[str]:
        record = self.get(record_id)
        return list(record.causes) if record else []

    def all(self) -> list[Record]:
        return [self._records[rid] for rid in self._append_order]

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        return filter_records(self.all(), expression)


class SQLiteStorage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._session() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS records (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    author TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    schema TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    causes TEXT NOT NULL,
                    authorization TEXT NOT NULL,
                    signature TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cause_edges (
                    parent_id TEXT NOT NULL,
                    child_id TEXT NOT NULL,
                    FOREIGN KEY(child_id) REFERENCES records(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_cause_parent ON cause_edges(parent_id);
                CREATE INDEX IF NOT EXISTS idx_cause_child ON cause_edges(child_id);
                """
            )

    def append(self, record: Record) -> None:
        if self.exists(record.id):
            raise ValueError(f"record already exists: {record.id}")
        with self._session() as conn:
            conn.execute(
                """
                INSERT INTO records (id, type, author, timestamp, schema, payload, causes, authorization, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.type.value,
                    record.author,
                    record.timestamp.isoformat(),
                    record.schema,
                    json.dumps(_to_plain(record.payload), sort_keys=True),
                    json.dumps(list(record.causes)),
                    json.dumps(list(record.authorization)),
                    record.signature,
                ),
            )
            for parent in record.causes:
                conn.execute(
                    "INSERT INTO cause_edges (parent_id, child_id) VALUES (?, ?)",
                    (parent, record.id),
                )

    def get(self, record_id: str) -> Record | None:
        with self._session() as conn:
            row = conn.execute(
                """
                SELECT id, type, author, timestamp, schema, payload, causes, authorization, signature
                FROM records
                WHERE id = ?
                """,
                (record_id,),
            ).fetchone()
        return _row_to_record(row) if row else None

    def exists(self, record_id: str) -> bool:
        with self._session() as conn:
            row = conn.execute("SELECT 1 FROM records WHERE id = ? LIMIT 1", (record_id,)).fetchone()
        return row is not None

    def children(self, record_id: str) -> list[Record]:
        with self._session() as conn:
            rows = conn.execute(
                """
                SELECT r.id, r.type, r.author, r.timestamp, r.schema, r.payload, r.causes, r.authorization, r.signature
                FROM cause_edges ce
                JOIN records r ON r.id = ce.child_id
                WHERE ce.parent_id = ?
                ORDER BY r.seq ASC
                """,
                (record_id,),
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def parents(self, record_id: str) -> list[str]:
        record = self.get(record_id)
        return list(record.causes) if record else []

    def all(self) -> list[Record]:
        with self._session() as conn:
            rows = conn.execute(
                """
                SELECT id, type, author, timestamp, schema, payload, causes, authorization, signature
                FROM records
                ORDER BY seq ASC
                """
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        return filter_records(self.all(), expression)


class LMDBStorage:
    def __init__(self, db_path: str, map_size: int = 64 * 1024 * 1024) -> None:
        if _lmdb is None:
            raise RuntimeError("lmdb package is required for LMDBStorage")
        os.makedirs(db_path, exist_ok=True)
        self._env = _lmdb.open(
            db_path,
            map_size=map_size,
            subdir=True,
            max_dbs=3,
            create=True,
            readahead=False,
        )
        self._records_db = self._env.open_db(b"records")
        self._sequence_db = self._env.open_db(b"sequence")
        self._children_db = self._env.open_db(b"children")
        self._closed = False

    def append(self, record: Record) -> None:
        record_key = _b(record.id)
        with self._env.begin(write=True) as txn:
            if txn.get(record_key, db=self._records_db) is not None:
                raise ValueError(f"record already exists: {record.id}")

            seq = _next_sequence(txn, self._sequence_db)
            txn.put(_seq_key(seq), record_key, db=self._sequence_db)
            txn.put(record_key, _record_to_json_bytes(record), db=self._records_db)

            for parent in record.causes:
                edge_key = _b(f"{parent}\x1f{record.id}")
                txn.put(edge_key, b"1", db=self._children_db)

    def get(self, record_id: str) -> Record | None:
        with self._env.begin() as txn:
            payload = txn.get(_b(record_id), db=self._records_db)
        if payload is None:
            return None
        return _json_bytes_to_record(payload)

    def exists(self, record_id: str) -> bool:
        with self._env.begin() as txn:
            return txn.get(_b(record_id), db=self._records_db) is not None

    def children(self, record_id: str) -> list[Record]:
        prefix = _b(f"{record_id}\x1f")
        records: list[Record] = []
        with self._env.begin() as txn:
            cursor = txn.cursor(db=self._children_db)
            found = cursor.set_range(prefix)
            while found:
                key = bytes(cursor.key())
                if not key.startswith(prefix):
                    break
                child_id = key.decode("utf-8").split("\x1f", 1)[1]
                payload = txn.get(_b(child_id), db=self._records_db)
                if payload is not None:
                    records.append(_json_bytes_to_record(bytes(payload)))
                found = cursor.next()
        return records

    def parents(self, record_id: str) -> list[str]:
        record = self.get(record_id)
        return list(record.causes) if record else []

    def all(self) -> list[Record]:
        records: list[Record] = []
        with self._env.begin() as txn:
            cursor = txn.cursor(db=self._sequence_db)
            for _, raw_record_id in cursor:
                payload = txn.get(bytes(raw_record_id), db=self._records_db)
                if payload is not None:
                    records.append(_json_bytes_to_record(bytes(payload)))
        return records

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        return filter_records(self.all(), expression)

    def close(self) -> None:
        if not self._closed:
            self._env.close()
            self._closed = True

    def __del__(self) -> None:
        if hasattr(self, "_closed") and not self._closed:
            self._env.close()
            self._closed = True


class RocksDBStorage:
    def __init__(self, db_path: str) -> None:
        if _Rdict is None:
            raise RuntimeError("rocksdict package is required for RocksDBStorage")
        os.makedirs(db_path, exist_ok=True)
        self._db = _Rdict(db_path)
        self._closed = False

    def append(self, record: Record) -> None:
        record_key = f"record:{record.id}"
        if record_key in self._db:
            raise ValueError(f"record already exists: {record.id}")

        seq = int(self._db.get("meta:last_seq", 0)) + 1
        self._db["meta:last_seq"] = seq
        self._db[f"seq:{seq:020d}"] = record.id
        self._db[record_key] = json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
        for parent in record.causes:
            self._db[f"child:{parent}\x1f{record.id}"] = "1"
            index_key = _rocks_children_index_key(parent)
            raw = self._db.get(index_key)
            child_ids = json.loads(str(raw)) if raw is not None else []
            child_ids.append(record.id)
            self._db[index_key] = json.dumps(child_ids, separators=(",", ":"))

    def get(self, record_id: str) -> Record | None:
        payload = self._db.get(f"record:{record_id}")
        if payload is None:
            return None
        data = json.loads(str(payload))
        return _dict_to_record(data)

    def exists(self, record_id: str) -> bool:
        return f"record:{record_id}" in self._db

    def children(self, record_id: str) -> list[Record]:
        index_key = _rocks_children_index_key(record_id)
        raw = self._db.get(index_key)
        if raw is not None:
            child_ids = [str(value) for value in json.loads(str(raw))]
        else:
            prefix = f"child:{record_id}\x1f"
            child_ids = [str(k).split("\x1f", 1)[1] for k in self._db.keys() if str(k).startswith(prefix)]
        return [record for record in (self.get(child_id) for child_id in child_ids) if record is not None]

    def parents(self, record_id: str) -> list[str]:
        record = self.get(record_id)
        return list(record.causes) if record else []

    def all(self) -> list[Record]:
        ordered_ids = [str(self._db[k]) for k in self._db.keys() if str(k).startswith("seq:")]
        return [record for record in (self.get(record_id) for record_id in ordered_ids) if record is not None]

    def query(self, expression: Mapping[str, Any]) -> list[Record]:
        return filter_records(self.all(), expression)

    def close(self) -> None:
        if not self._closed:
            self._db.close()
            self._closed = True

    def __del__(self) -> None:
        if hasattr(self, "_closed") and not self._closed:
            self._db.close()
            self._closed = True


def _row_to_record(row: tuple[Any, ...]) -> Record:
    return Record(
        id=str(row[0]),
        type=PrimitiveType(str(row[1])),
        author=str(row[2]),
        timestamp=datetime.fromisoformat(str(row[3])),
        schema=str(row[4]),
        payload=json.loads(str(row[5])),
        causes=tuple(json.loads(str(row[6]))),
        authorization=tuple(json.loads(str(row[7]))),
        signature=str(row[8]),
    )


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def _record_to_json_bytes(record: Record) -> bytes:
    return json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")


def _json_bytes_to_record(payload: bytes) -> Record:
    data = json.loads(payload.decode("utf-8"))
    return _dict_to_record(data)


def _dict_to_record(data: Mapping[str, Any]) -> Record:
    return Record(
        id=str(data["id"]),
        type=PrimitiveType(str(data["type"])),
        author=str(data["author"]),
        timestamp=datetime.fromisoformat(str(data["timestamp"])),
        schema=str(data["schema"]),
        payload=data["payload"],
        causes=tuple(data.get("causes", [])),
        authorization=tuple(data.get("authorization", [])),
        signature=str(data["signature"]),
    )


def _b(value: str) -> bytes:
    return value.encode("utf-8")


def _seq_key(seq: int) -> bytes:
    return f"{seq:020d}".encode("utf-8")


def _next_sequence(txn: Any, sequence_db: Any) -> int:
    cursor = txn.cursor(db=sequence_db)
    if not cursor.last():
        return 1
    last_key = bytes(cursor.key()).decode("utf-8")
    return int(last_key) + 1


def _rocks_children_index_key(parent_id: str) -> str:
    return f"children:{parent_id}"
