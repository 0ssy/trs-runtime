from __future__ import annotations

import uvicorn

from .server import create_app

app = create_app()


def main() -> None:
    uvicorn.run("node.app:app", host="127.0.0.1", port=8080, reload=False)


if __name__ == "__main__":
    main()
