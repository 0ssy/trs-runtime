from __future__ import annotations

import unittest

from terranode.terranode.semantics import MappingCommitment, SemanticRegistry


class Program6SemanticInteropTests(unittest.TestCase):
    def test_comparison_undefined_without_mapping_and_defined_with_mapping(self) -> None:
        registry = SemanticRegistry()
        self.assertIsNone(
            registry.compare_terms(
                community_a="community-a",
                term_a="household",
                community_b="community-b",
                term_b="household",
            )
        )

        registry.add_mapping_commitment(
            MappingCommitment(
                record_id="map-a-1",
                from_community="community-a",
                from_term="household",
                canonical_term="canonical:household-unit",
            )
        )
        registry.add_mapping_commitment(
            MappingCommitment(
                record_id="map-b-1",
                from_community="community-b",
                from_term="household",
                canonical_term="canonical:household-unit",
            )
        )
        self.assertTrue(
            registry.compare_terms(
                community_a="community-a",
                term_a="household",
                community_b="community-b",
                term_b="household",
            )
        )


if __name__ == "__main__":
    unittest.main()
