from __future__ import annotations

import asyncio
from typing import Callable
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api import health, query, record, replay, submit, sync
from .config import NodeConfig
from .runtime_service import RuntimeService


def create_app(config: NodeConfig | None = None, service: RuntimeService | None = None) -> FastAPI:
    resolved_config = config or NodeConfig()
    resolved_service = service or RuntimeService()
    app = FastAPI(title="trs-node", version=resolved_config.node_version)

    @app.middleware("http")
    async def request_limits_and_ids(request: Request, call_next: Callable):
        request_id = str(uuid.uuid4())
        body = await request.body()
        if len(body) > resolved_config.max_request_bytes:
            return JSONResponse(
                status_code=413,
                content={"error": "request too large", "request_id": request_id},
            )
        async def process():
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        try:
            return await asyncio.wait_for(process(), timeout=resolved_config.request_timeout_seconds)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"error": "request timed out", "request_id": request_id},
            )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"error": str(exc)})

    app.include_router(health.router(resolved_config))
    app.include_router(submit.router(resolved_service))
    app.include_router(record.router(resolved_service))
    app.include_router(query.router(resolved_service))
    app.include_router(sync.router(resolved_service))
    app.include_router(replay.router(resolved_service))
    return app
