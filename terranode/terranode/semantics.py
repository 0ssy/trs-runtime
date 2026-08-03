from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MappingCommitment:
    record_id: str
    from_community: str
    from_term: str
    canonical_term: str


class SemanticRegistry:
    def __init__(self) -> None:
        self._mappings: dict[tuple[str, str], str] = {}
        self._commitments: list[MappingCommitment] = []

    def add_mapping_commitment(self, commitment: MappingCommitment) -> None:
        key = (commitment.from_community, commitment.from_term)
        self._mappings[key] = commitment.canonical_term
        self._commitments.append(commitment)

    def compare_terms(self, *, community_a: str, term_a: str, community_b: str, term_b: str) -> bool | None:
        canonical_a = self._mappings.get((community_a, term_a))
        canonical_b = self._mappings.get((community_b, term_b))
        if canonical_a is None or canonical_b is None:
            return None
        return canonical_a == canonical_b

    @property
    def commitments(self) -> list[MappingCommitment]:
        return list(self._commitments)
