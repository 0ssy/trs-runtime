from __future__ import annotations

import unittest

from terranode.terranode.privacy import PrivacyCredential, verify_selective_disclosure


class Program911PrivacyTests(unittest.TestCase):
    def test_selective_disclosure_proves_required_attributes_only(self) -> None:
        credential = PrivacyCredential(
            {
                "membership": "village-coop",
                "age_over_18": "true",
                "allocation_tier": "critical",
                "full_name": "alice-private",
            }
        )
        proof = credential.selective_disclose(["membership", "age_over_18"])

        self.assertNotIn("full_name", proof.disclosed)
        self.assertTrue(
            verify_selective_disclosure(
                proof,
                required_keys=["membership", "age_over_18"],
            )
        )


if __name__ == "__main__":
    unittest.main()
