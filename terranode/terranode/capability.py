from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityToken:
    token_id: str
    subject: str
    grantee: str
    expires_at_epoch: int
    issuer_token_id: str | None


class CapabilityRegistry:
    def __init__(self) -> None:
        self._tokens: dict[str, CapabilityToken] = {}
        self._superseded: set[str] = set()

    def issue(self, token: CapabilityToken) -> None:
        self._tokens[token.token_id] = token

    def supersede(self, old_token_id: str, replacement: CapabilityToken) -> None:
        self._superseded.add(old_token_id)
        self._tokens[replacement.token_id] = replacement

    def validate(self, *, token_id: str, subject: str, actor: str, now_epoch: int) -> tuple[bool, str]:
        token = self._tokens.get(token_id)
        if token is None:
            return False, "unknown capability"
        if token_id in self._superseded:
            return False, "capability superseded"
        if token.subject != subject:
            return False, "capability scope mismatch"
        if token.grantee != actor:
            return False, "capability grantee mismatch"
        if token.expires_at_epoch < now_epoch:
            return False, "capability expired"
        if token.issuer_token_id is not None:
            return False, "non-transitive delegation denied"
        return True, "ok"
