from __future__ import annotations

from typing import Any

from runtime.record import Record


def record_to_json(record: Record) -> dict[str, Any]:
    return record.to_dict()
