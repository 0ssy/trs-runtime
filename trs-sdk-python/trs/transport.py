from __future__ import annotations

import json
import socket
from typing import Any
from urllib import error, request

from .exceptions import TRSConnectionError, TRSServerError, TRSValidationError


class HTTPTransport:
    def __init__(self, base_url: str, *, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get(self, path: str) -> Any:
        return self._send("GET", path, None)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        return self._send("POST", path, payload)

    def _send(self, method: str, path: str, payload: dict[str, Any] | None) -> Any:
        url = f"{self.base_url}{path}"
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url=url, method=method, data=body, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except error.HTTPError as exc:
            message = self._extract_http_error_message(exc)
            if 400 <= exc.code < 500:
                raise TRSValidationError(message) from exc
            raise TRSServerError(message) from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise TRSConnectionError(str(exc)) from exc

        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise TRSServerError("invalid JSON response from trs-node") from exc

    def _extract_http_error_message(self, exc: error.HTTPError) -> str:
        try:
            payload = exc.read().decode("utf-8")
            if not payload:
                return f"http {exc.code}"
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                if "detail" in parsed:
                    return str(parsed["detail"])
                if "error" in parsed:
                    return str(parsed["error"])
            return payload
        except Exception:
            return f"http {exc.code}"

