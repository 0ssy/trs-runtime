from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
from typing import Any, Mapping
import uuid

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from .canonical import canonical_record_bytes as _canonical_record_bytes
from .record import Record


@dataclass(frozen=True)
class SigningKey:
    author: str
    key_id: str
    private_key_b64: str
    public_key_b64: str
    created_at: datetime
    active: bool


class CryptoSuite:
    def __init__(self) -> None:
        self._public_keys: dict[str, dict[str, Ed25519PublicKey]] = {}
        self._active_key: dict[str, str] = {}
        self._revision: int = 0

    def generate_key(self, author: str, *, set_active: bool = True) -> SigningKey:
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        key_id = str(uuid.uuid4())
        private_raw = private_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption(),
        )
        public_raw = public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)
        private_b64 = base64.b64encode(private_raw).decode("utf-8")
        public_b64 = base64.b64encode(public_raw).decode("utf-8")
        self.register_public_key(author, key_id, public_b64, set_active=set_active)
        return SigningKey(
            author=author,
            key_id=key_id,
            private_key_b64=private_b64,
            public_key_b64=public_b64,
            created_at=datetime.now(timezone.utc),
            active=set_active,
        )

    def rotate_key(self, author: str) -> SigningKey:
        return self.generate_key(author, set_active=True)

    def register_public_key(
        self, author: str, key_id: str, public_key_b64: str, *, set_active: bool = False
    ) -> None:
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        self._public_keys.setdefault(author, {})[key_id] = public_key
        if set_active or author not in self._active_key:
            self._active_key[author] = key_id
        self._revision += 1

    def revision(self) -> int:
        return self._revision

    def export_public_keys(self) -> dict[str, dict[str, str]]:
        bundle: dict[str, dict[str, str]] = {}
        for author, keys in self._public_keys.items():
            encoded: dict[str, str] = {}
            for key_id, public_key in keys.items():
                raw = public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)
                encoded[key_id] = base64.b64encode(raw).decode("utf-8")
            bundle[author] = encoded
        return bundle

    def import_public_keys(self, bundle: Mapping[str, Mapping[str, str]]) -> None:
        changed = False
        for author, keys in bundle.items():
            author_keys = self._public_keys.setdefault(author, {})
            for key_id, public_b64 in keys.items():
                if key_id in author_keys:
                    continue
                author_keys[key_id] = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_b64))
                if author not in self._active_key:
                    self._active_key[author] = key_id
                changed = True
        if changed:
            self._revision += 1

    def sign_record(self, record: Record, private_key_b64: str, key_id: str) -> str:
        private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
        payload = _canonical_record_bytes(record, include_signature=False)
        sig_b64 = base64.b64encode(private_key.sign(payload)).decode("utf-8")
        return f"ed25519:{key_id}:{sig_b64}"

    def verify_record_signature(self, record: Record) -> tuple[bool, str]:
        parts = record.signature.split(":")
        if len(parts) != 3 or parts[0] != "ed25519":
            return False, "signature format invalid for Ed25519"
        key_id = parts[1]
        sig_b64 = parts[2]
        public_key = self._public_keys.get(record.author, {}).get(key_id)
        if public_key is None:
            return False, f"unknown key id {key_id} for author {record.author}"
        payload = _canonical_record_bytes(record, include_signature=False)
        try:
            public_key.verify(base64.b64decode(sig_b64), payload)
        except Exception:
            return False, "signature verification failed"
        return True, ""


def clone_with_signature(record: Record, signature: str) -> Record:
    return Record(
        id=record.id,
        type=record.type,
        author=record.author,
        timestamp=record.timestamp,
        schema=record.schema,
        payload=record.payload,
        causes=record.causes,
        authorization=record.authorization,
        signature=signature,
        subject=record.subject,
    )


def canonical_record_bytes(record: Record) -> bytes:
    return _canonical_record_bytes(record, include_signature=False)
