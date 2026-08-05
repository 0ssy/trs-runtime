from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "evidence" / "interop"
LATEST_PATH = EVIDENCE_DIR / "cycle0012_sdk_cross_runtime_latest.json"


@dataclass(frozen=True)
class SdkFlowResult:
    sdk: str
    health_ok: bool
    submit_accepted: bool
    sync_accepted_count: int
    sync_rejected_count: int
    query_author_count: int
    replay_unresolved_intentions: list[str]
    artifact_path: str


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_health(base_url: str, timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    health_url = f"{base_url}/health"
    while time.time() < deadline:
        try:
            request = Request(health_url, method="GET")
            with urlopen(request, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
            continue
    raise RuntimeError(f"server did not become healthy: {health_url}")


def _run_rust_sdk_flow(base_url: str, output_path: Path) -> dict[str, Any]:
    command = [
        "cargo",
        "run",
        "--quiet",
        "--example",
        "interop_node_flow",
        "--",
        base_url,
        str(output_path),
    ]
    subprocess.run(command, cwd=ROOT / "trs-sdk-rust", check=True)
    return json.loads(output_path.read_text(encoding="utf-8"))


def _run_java_sdk_flow(base_url: str, output_path: Path) -> dict[str, Any]:
    java_root = ROOT / "trs-sdk-java"
    build_dir = java_root / "build" / "classes"
    build_dir.mkdir(parents=True, exist_ok=True)
    main_java = sorted((java_root / "src" / "main" / "java").rglob("*.java"))
    interop_java = java_root / "tests" / "InteropNodeFlow.java"
    compile_command = ["javac", "-d", str(build_dir)] + [str(path) for path in main_java] + [str(interop_java)]
    subprocess.run(compile_command, check=True)
    run_command = [
        "java",
        "-cp",
        str(build_dir),
        "dev.trs.sdk.InteropNodeFlow",
        base_url,
        str(output_path),
    ]
    subprocess.run(run_command, check=True)
    return json.loads(output_path.read_text(encoding="utf-8"))


def _to_result(payload: dict[str, Any], artifact_path: Path) -> SdkFlowResult:
    replay_unresolved = payload.get("replay_unresolved_intentions")
    unresolved = []
    if isinstance(replay_unresolved, list):
        unresolved = [str(value) for value in replay_unresolved]
    health = payload.get("health") if isinstance(payload.get("health"), dict) else {}
    submit = payload.get("submit") if isinstance(payload.get("submit"), dict) else {}
    sync = payload.get("sync") if isinstance(payload.get("sync"), dict) else {}
    return SdkFlowResult(
        sdk=str(payload.get("sdk", "")),
        health_ok=health.get("status") == "ok",
        submit_accepted=bool(submit.get("accepted", False)),
        sync_accepted_count=int(sync.get("accepted_count", 0)),
        sync_rejected_count=int(sync.get("rejected_count", 0)),
        query_author_count=int(payload.get("query_author_count", 0)),
        replay_unresolved_intentions=unresolved,
        artifact_path=str(artifact_path.relative_to(ROOT)),
    )


def run_cycle_0012_sdk_cross_runtime() -> dict[str, Any]:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    db_path = EVIDENCE_DIR / f"{timestamp}_cycle0012_sdk_cross_runtime.db"
    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"

    node_command = [
        str(ROOT / "venv" / "Scripts" / "python.exe"),
        "-m",
        "node.app",
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--db",
        str(db_path),
    ]
    node_log_path = EVIDENCE_DIR / f"{timestamp}_cycle0012_sdk_cross_runtime_node.log"
    pythonpath_parts = [str(ROOT), str(ROOT / "trs-node")]
    existing_pythonpath = os.environ.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    node_log = node_log_path.open("w", encoding="utf-8")
    node_process = subprocess.Popen(
        node_command,
        cwd=ROOT,
        stdout=node_log,
        stderr=node_log,
        env=env,
    )
    records: list[dict[str, Any]] = []
    try:
        _wait_health(base_url, timeout_seconds=30.0)

        rust_artifact = EVIDENCE_DIR / f"{timestamp}_cycle0012_rust_sdk_flow.json"
        rust_payload = _run_rust_sdk_flow(base_url, rust_artifact)
        rust_result = _to_result(rust_payload, rust_artifact)

        java_artifact = EVIDENCE_DIR / f"{timestamp}_cycle0012_java_sdk_flow.json"
        java_payload = _run_java_sdk_flow(base_url, java_artifact)
        java_result = _to_result(java_payload, java_artifact)

        request = Request(
            f"{base_url}/query",
            data=json.dumps({"query": {}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = payload.get("records")
        if isinstance(rows, list):
            records = [row for row in rows if isinstance(row, dict)]
    finally:
        node_process.terminate()
        try:
            node_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            node_process.kill()
            node_process.wait(timeout=5)
        node_log.close()

    ids = sorted(str(row.get("id", "")) for row in records)
    summary = {
        "timestamp": timestamp,
        "base_url": base_url,
        "db_path": str(db_path.relative_to(ROOT)),
        "node_log_path": str(node_log_path.relative_to(ROOT)),
        "rust": asdict(rust_result),
        "java": asdict(java_result),
        "record_count": len(records),
        "record_ids": ids,
        "cross_runtime_pass": (
            rust_result.health_ok
            and rust_result.submit_accepted
            and rust_result.sync_accepted_count >= 1
            and rust_result.sync_rejected_count == 0
            and rust_result.query_author_count >= 1
            and java_result.health_ok
            and java_result.submit_accepted
            and java_result.sync_accepted_count >= 1
            and java_result.sync_rejected_count == 0
            and java_result.query_author_count >= 1
            and "rust-int-1" in ids
            and "java-int-1" in ids
        ),
    }
    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0012_sdk_cross_runtime_summary.json"
    summary["summary_path"] = str(summary_path.relative_to(ROOT))
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    out = run_cycle_0012_sdk_cross_runtime()
    print(f"Summary: {out['summary_path']}")
    print(f"Cross-runtime pass: {out['cross_runtime_pass']}")
