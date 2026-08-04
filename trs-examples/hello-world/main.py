from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import client, observation


def main() -> None:
    c = client()
    record = observation(author="example-hello", subject="hello-world", value={"message": "Hello, TRS"})
    result = c.submit(record)
    fetched = c.query({"cause": record["id"]})
    print({"submitted": result.record_id, "children": len(fetched)})


if __name__ == "__main__":
    main()
