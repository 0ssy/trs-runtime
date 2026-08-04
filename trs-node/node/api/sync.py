from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..runtime_service import RuntimeService


def router(service: RuntimeService) -> APIRouter:
    api = APIRouter()

    @api.post("/sync")
    def sync(payload: dict[str, Any]) -> dict[str, Any]:
        records = payload.get("records")
        if not isinstance(records, list):
            raise HTTPException(status_code=422, detail="field 'records' must be an array")
        if not all(isinstance(record, dict) for record in records):
            raise HTTPException(status_code=422, detail="all items in 'records' must be objects")
        try:
            outcome = service.sync(records)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "accepted_count": outcome.accepted_count,
            "rejected_count": outcome.rejected_count,
            "appended_ids": outcome.appended_ids,
            "rejected_errors": outcome.rejected_errors,
        }

    return api
