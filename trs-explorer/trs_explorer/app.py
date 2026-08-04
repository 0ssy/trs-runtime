from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn

from .service import ExplorerService


def create_app(service: ExplorerService | None = None) -> FastAPI:
    app = FastAPI(title="trs-explorer", version="0.1.0")
    explorer = service or ExplorerService(base_url=os.getenv("TRS_NODE_URL", "http://127.0.0.1:8080"))

    static_dir = Path(__file__).resolve().parent / "static"

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/styles.css")
    def styles() -> FileResponse:
        return FileResponse(static_dir / "styles.css")

    @app.get("/app.js")
    def script() -> FileResponse:
        return FileResponse(static_dir / "app.js")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return explorer.health()

    @app.get("/api/records")
    def records(search: str = "") -> dict[str, Any]:
        return explorer.graph_payload(search=search)

    @app.get("/api/replay")
    def replay() -> dict[str, Any]:
        return explorer.fetch_replay()

    @app.post("/api/explain")
    def explain(payload: dict[str, Any]) -> dict[str, Any]:
        record = payload.get("record")
        if not isinstance(record, dict):
            raise HTTPException(status_code=422, detail="field 'record' must be an object")
        return explorer.explain(record)

    return app


app = create_app()


def main() -> None:
    uvicorn.run("trs_explorer.app:app", host="127.0.0.1", port=8090, reload=False)


if __name__ == "__main__":
    main()

