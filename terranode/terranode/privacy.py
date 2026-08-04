from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SelectiveDisclosureProof:
    root_hash: str
    disclosed: dict[str, str]
    disclosed_salts: dict[str, str]
    all_leaf_hashes: dict[str, str]


class PrivacyCredential:
    def __init__(self, claims: dict[str, str], *, namespace: str = "terranode-privacy") -> None:
        self.claims = dict(claims)
        self.namespace = namespace
        self.salts = {key: _hash_text(f"{namespace}:{key}")[:16] for key in claims}
        self.leaf_hashes = {
            key: _hash_text(f"{key}:{claims[key]}:{self.salts[key]}")
            for key in claims
        }
        self.root_hash = _hash_text(
            json.dumps(sorted(self.leaf_hashes.values()), separators=(",", ":"))
        )

    def selective_disclose(self, keys: list[str]) -> SelectiveDisclosureProof:
        disclosed = {key: self.claims[key] for key in keys if key in self.claims}
        disclosed_salts = {key: self.salts[key] for key in disclosed}
        return SelectiveDisclosureProof(
            root_hash=self.root_hash,
            disclosed=disclosed,
            disclosed_salts=disclosed_salts,
            all_leaf_hashes=dict(self.leaf_hashes),
        )


def verify_selective_disclosure(
    proof: SelectiveDisclosureProof,
    *,
    required_keys: list[str],
) -> bool:
    for key in required_keys:
        if key not in proof.disclosed or key not in proof.disclosed_salts:
            return False
        expected = _hash_text(f"{key}:{proof.disclosed[key]}:{proof.disclosed_salts[key]}")
        if proof.all_leaf_hashes.get(key) != expected:
            return False
    reconstructed_root = _hash_text(
        json.dumps(sorted(proof.all_leaf_hashes.values()), separators=(",", ":"))
    )
    return reconstructed_root == proof.root_hash
