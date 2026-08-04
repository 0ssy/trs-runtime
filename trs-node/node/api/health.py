from __future__ import annotations

from fastapi import APIRouter

from ..config import NodeConfig


def router(config: NodeConfig) -> APIRouter:
    api = APIRouter()

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "runtime": config.runtime_version, "node": config.node_version}

    return api
