from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import sys
import uuid

REPO_ROOT = Path(__file__).resolve().parents[1]
SDK_ROOT = REPO_ROOT / "trs-sdk-python"
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

from trs import Client


def node_url() -> str:
    return os.getenv("TRS_NODE_URL", "http://127.0.0.1:8080")


def client() -> Client:
    return Client(node_url())


def record_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def observation(*, author: str, subject: str, value: object, causes: list[str] | None = None) -> dict:
    return {
        "id": record_id("obs"),
        "type": "Observation",
        "author": author,
        "timestamp": now_iso(),
        "schema": "trs.observation.v1",
        "payload": {"subject": subject, "value": value},
        "causes": causes or [],
        "authorization": [],
        "signature": f"sig:{record_id('sig')}",
        "subject": subject,
    }


def intention(*, author: str, subject: str, goal: str, horizon: str, causes: list[str]) -> dict:
    return {
        "id": record_id("int"),
        "type": "Intention",
        "author": author,
        "timestamp": now_iso(),
        "schema": "trs.intention.v1",
        "payload": {"goal": goal, "horizon": horizon},
        "causes": causes,
        "authorization": [],
        "signature": f"sig:{record_id('sig')}",
        "subject": subject,
    }


def commitment(
    *,
    author: str,
    subject: str,
    action: str,
    due_by: str,
    causes: list[str],
    authorization: list[str] | None = None,
    extra: dict | None = None,
) -> dict:
    payload = {"action": action, "due_by": due_by}
    if extra:
        payload.update(extra)
    return {
        "id": record_id("com"),
        "type": "Commitment",
        "author": author,
        "timestamp": now_iso(),
        "schema": "trs.commitment.v1",
        "payload": payload,
        "causes": causes,
        "authorization": authorization or [],
        "signature": f"sig:{record_id('sig')}",
        "subject": subject,
    }
