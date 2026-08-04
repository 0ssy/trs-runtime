from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    status: str
    runtime: str
    node: str


@dataclass(frozen=True)
class SubmitResult:
    accepted: bool
    record_id: str
    errors: list[str]


@dataclass(frozen=True)
class SyncResult:
    accepted_count: int
    rejected_count: int
    appended_ids: list[str]
    rejected_errors: list[list[str]]

