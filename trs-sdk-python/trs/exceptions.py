from __future__ import annotations


class TRSError(Exception):
    """Base SDK exception."""


class TRSConnectionError(TRSError):
    """Network or timeout failure."""


class TRSValidationError(TRSError):
    """Validation failure from trs-node or runtime verifier."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class TRSServerError(TRSError):
    """Server-side failure."""


class TRSProtocolError(TRSError):
    """Unexpected response shape."""

