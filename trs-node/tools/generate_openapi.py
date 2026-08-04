from __future__ import annotations

import json
from pathlib import Path

from node.server import create_app


def main() -> None:
    app = create_app()
    schema = app.openapi()
    out_dir = Path(__file__).resolve().parents[1] / "openapi"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "trs-node.openapi.json"
    out_file.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
    print(out_file)


if __name__ == "__main__":
    main()

