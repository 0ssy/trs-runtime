from __future__ import annotations

from trs import Client


def main() -> None:
    source = Client("http://localhost:8080")
    target = Client("http://localhost:8081")
    records = source.query({})
    print(target.sync(records))


if __name__ == "__main__":
    main()

