from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..runtime_service import RuntimeService


def router(service: RuntimeService) -> APIRouter:
    api = APIRouter()

    @api.post("/submit")
    def submit(payload: dict[str, Any]) -> dict[str, Any]:
        record = payload.get("record")
        if not isinstance(record, dict):
            raise HTTPException(status_code=422, detail="field 'record' must be an object")
        try:
            outcome = service.submit(record)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "accepted": outcome.accepted,
            "record_id": outcome.record_id,
            "errors": outcome.errors,
        }

    return api
