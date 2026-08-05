from __future__ import annotations

import argparse
import sys

import uvicorn

from runtime.storage import SQLiteStorage

from .config import NodeConfig
from .runtime_service import RuntimeService
from .server import create_app


def _build_runtime_service(db_path: str | None) -> RuntimeService:
    if db_path is None:
        return RuntimeService()
    return RuntimeService(store=SQLiteStorage(db_path))


def build_app(config: NodeConfig | None = None) -> object:
    resolved_config = config or NodeConfig()
    service = _build_runtime_service(resolved_config.db_path)
    return create_app(config=resolved_config, service=service)


app = build_app()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trs-node")
    serve = parser.add_subparsers(dest="command").add_parser("serve", help="Run trs-node HTTP server")
    defaults = NodeConfig()
    serve.add_argument("--host", default=defaults.host, help="Bind host (default from TRS_NODE_HOST or 127.0.0.1)")
    serve.add_argument("--port", type=int, default=defaults.port, help="Bind port (default from TRS_NODE_PORT or 8080)")
    serve.add_argument("--db", default=defaults.db_path, help="SQLite database path for persistent append-only storage")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    parsed = parser.parse_args(argv)
    command = parsed.command or "serve"
    if command != "serve":
        parser.error(f"unsupported command: {command}")
    config = NodeConfig(host=parsed.host, port=parsed.port, db_path=parsed.db)
    run_app = build_app(config=config)
    uvicorn.run(run_app, host=config.host, port=config.port, reload=False)


if __name__ == "__main__":
    main(sys.argv[1:])
