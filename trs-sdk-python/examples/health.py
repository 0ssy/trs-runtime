from __future__ import annotations

from trs import Client


def main() -> None:
    client = Client("http://localhost:8080")
    print(client.health())


if __name__ == "__main__":
    main()

