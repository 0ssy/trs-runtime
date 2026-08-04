from __future__ import annotations

from fastapi import APIRouter

from ..runtime_service import RuntimeService


def router(service: RuntimeService) -> APIRouter:
    api = APIRouter()

    @api.post("/replay")
    def replay() -> dict:
        return service.replay()

    return api
