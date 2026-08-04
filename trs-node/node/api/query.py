from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..runtime_service import RuntimeService
from ..serialization import record_to_json


def router(service: RuntimeService) -> APIRouter:
    api = APIRouter()

    @api.post("/query")
    def query(payload: dict[str, Any]) -> dict[str, Any]:
        expression = payload.get("query")
        if not isinstance(expression, dict):
            raise HTTPException(status_code=422, detail="field 'query' must be an object")
        records = service.query(expression)
        return {"records": [record_to_json(record) for record in records]}

    return api
