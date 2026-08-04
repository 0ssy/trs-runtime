from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class NodeConfig:
    host: str = os.getenv("TRS_NODE_HOST", "127.0.0.1")
    port: int = int(os.getenv("TRS_NODE_PORT", "8080"))
    request_timeout_seconds: float = float(os.getenv("TRS_NODE_REQUEST_TIMEOUT_SECONDS", "10"))
    max_request_bytes: int = int(os.getenv("TRS_NODE_MAX_REQUEST_BYTES", str(1024 * 1024)))
    runtime_version: str = os.getenv("TRS_RUNTIME_VERSION", "1.0.0")
    node_version: str = "0.1.0"
