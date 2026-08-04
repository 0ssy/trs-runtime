from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from trs import Client, TRSConnectionError, TRSServerError, TRSValidationError


def _load_json_inline_or_file(inline: str | None, file_path: str | None, label: str) -> Any:
    if inline is not None and file_path is not None:
        raise ValueError(f"provide either --{label}-json or --{label}-file, not both")
    if inline is None and file_path is None:
        raise ValueError(f"missing required input: --{label}-json or --{label}-file")
    try:
        if inline is not None:
            return json.loads(inline)
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON for {label}: {exc}") from exc


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trs", description="TRS CLI client")
    parser.add_argument("--url", default="http://127.0.0.1:8080", help="trs-node base URL")
    parser.add_argument("--timeout-seconds", type=float, default=5.0, help="HTTP timeout in seconds")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="Check node health")

    submit = subparsers.add_parser("submit", help="Submit one record")
    submit.add_argument("--record-json")
    submit.add_argument("--record-file")

    query = subparsers.add_parser("query", help="Run query expression")
    query.add_argument("--expr-json")
    query.add_argument("--expr-file")

    sync = subparsers.add_parser("sync", help="Sync records into this node")
    sync.add_argument("--records-json")
    sync.add_argument("--records-file")

    subparsers.add_parser("replay", help="Replay derived state")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    client = Client(args.url, timeout_seconds=args.timeout_seconds)
    try:
        if args.command == "health":
            result = client.health()
            _print_json({"status": result.status, "runtime": result.runtime, "node": result.node})
            return 0
        if args.command == "submit":
            record = _load_json_inline_or_file(args.record_json, args.record_file, "record")
            if not isinstance(record, dict):
                raise ValueError("record must be a JSON object")
            result = client.submit(record)
            _print_json({"accepted": result.accepted, "record_id": result.record_id, "errors": result.errors})
            return 0
        if args.command == "query":
            expression = _load_json_inline_or_file(args.expr_json, args.expr_file, "expr")
            if not isinstance(expression, dict):
                raise ValueError("expr must be a JSON object")
            _print_json({"records": client.query(expression)})
            return 0
        if args.command == "sync":
            records = _load_json_inline_or_file(args.records_json, args.records_file, "records")
            if not isinstance(records, list):
                raise ValueError("records must be a JSON array")
            result = client.sync(records)
            _print_json(
                {
                    "accepted_count": result.accepted_count,
                    "rejected_count": result.rejected_count,
                    "appended_ids": result.appended_ids,
                    "rejected_errors": result.rejected_errors,
                }
            )
            return 0
        if args.command == "replay":
            _print_json(client.replay())
            return 0
        parser.error(f"unsupported command: {args.command}")
        return 2
    except (ValueError, TRSValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (TRSConnectionError, TRSServerError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

