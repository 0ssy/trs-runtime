from __future__ import annotations

from typing import Any


def parse_search(expression: str) -> dict[str, str]:
    criteria: dict[str, str] = {}
    for token in expression.split():
        if ":" not in token:
            continue
        key, value = token.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key and value:
            criteria[key] = value
    return criteria


def filter_records(
    records: list[dict[str, Any]],
    criteria: dict[str, str],
    unresolved_intentions: set[str] | None = None,
) -> list[dict[str, Any]]:
    unresolved = unresolved_intentions or set()
    filtered = records
    for key, value in criteria.items():
        lowered = value.lower()
        if key == "subject":
            filtered = [r for r in filtered if str(r.get("subject", "")).lower() == lowered]
        elif key == "author":
            filtered = [r for r in filtered if str(r.get("author", "")).lower() == lowered]
        elif key == "primitive":
            filtered = [r for r in filtered if str(r.get("type", "")).lower() == lowered]
        elif key == "schema":
            filtered = [r for r in filtered if str(r.get("schema", "")).lower() == lowered]
        elif key == "record":
            filtered = [r for r in filtered if str(r.get("id", "")).lower() == lowered]
        elif key == "status":
            if lowered == "open":
                filtered = [
                    r
                    for r in filtered
                    if str(r.get("type", "")).lower() == "intention" and str(r.get("id", "")) in unresolved
                ]
            elif lowered == "closed":
                filtered = [
                    r
                    for r in filtered
                    if str(r.get("type", "")).lower() != "intention" or str(r.get("id", "")) not in unresolved
                ]
    return filtered

