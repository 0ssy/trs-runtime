from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..runtime_service import RuntimeService


def router(service: RuntimeService) -> APIRouter:
    api = APIRouter()

    @api.get("/record/{id}")
    def get_record(id: str) -> dict:
        record = service.get_record(id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"record '{id}' not found")
        return record

    return api
