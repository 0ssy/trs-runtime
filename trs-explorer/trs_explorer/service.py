from __future__ import annotations

from datetime import datetime
from typing import Any

from trs import Client

from .search import filter_records, parse_search


class ExplorerService:
    def __init__(self, *, base_url: str = "http://127.0.0.1:8080", client: Client | None = None) -> None:
        self.client = client or Client(base_url)

    def health(self) -> dict[str, str]:
        status = self.client.health()
        return {"status": status.status, "runtime": status.runtime, "node": status.node}

    def fetch_records(self) -> list[dict[str, Any]]:
        return self.client.query({})

    def fetch_replay(self) -> dict[str, Any]:
        return self.client.replay()

    def explain(self, record: dict[str, Any]) -> dict[str, Any]:
        try:
            submitted = self.client.submit(record)
            return {"accepted": submitted.accepted, "errors": submitted.errors}
        except Exception as exc:
            errors = getattr(exc, "errors", None)
            if isinstance(errors, list):
                return {"accepted": False, "errors": [str(error) for error in errors]}
            return {"accepted": False, "errors": [str(exc)]}

    def graph_payload(self, search: str = "") -> dict[str, Any]:
        records = self.fetch_records()
        replay = self.fetch_replay()
        unresolved = set(
            str(v) for v in replay.get("coordination", {}).get("unresolved_intentions", [])
            if isinstance(v, str)
        )
        criteria = parse_search(search)
        visible = filter_records(records, criteria, unresolved)
        visible_ids = {str(record.get("id", "")) for record in visible}
        nodes = []
        for record in sorted(visible, key=_record_time_key):
            nodes.append(
                {
                    "id": str(record.get("id", "")),
                    "type": str(record.get("type", "")),
                    "author": str(record.get("author", "")),
                    "subject": str(record.get("subject", "")),
                    "schema": str(record.get("schema", "")),
                    "timestamp": str(record.get("timestamp", "")),
                    "status": _status_for_record(record, unresolved),
                    "causes": [str(v) for v in record.get("causes", []) if isinstance(v, str)],
                    "authorization": [str(v) for v in record.get("authorization", []) if isinstance(v, str)],
                }
            )

        edges = []
        children_map: dict[str, list[str]] = {}
        index = {str(record.get("id", "")): record for record in records}
        for record in records:
            rid = str(record.get("id", ""))
            for cause in record.get("causes", []):
                cause_id = str(cause)
                children_map.setdefault(cause_id, []).append(rid)
                if rid in visible_ids and cause_id in visible_ids:
                    edges.append({"from": cause_id, "to": rid})

        return {
            "nodes": nodes,
            "edges": edges,
            "children_map": children_map,
            "record_index": index,
            "replay": replay,
        }


def _record_time_key(record: dict[str, Any]) -> tuple[int, str]:
    raw = str(record.get("timestamp", ""))
    try:
        parsed = datetime.fromisoformat(raw)
        return (int(parsed.timestamp()), str(record.get("id", "")))
    except Exception:
        return (0, str(record.get("id", "")))


def _status_for_record(record: dict[str, Any], unresolved_intentions: set[str]) -> str:
    rid = str(record.get("id", ""))
    primitive = str(record.get("type", "")).lower()
    if primitive == "intention":
        return "Open" if rid in unresolved_intentions else "Closed"
    return "Verified"

