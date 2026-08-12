from __future__ import annotations

from datetime import datetime, timezone
import unittest

from hypothesis import given, settings, strategies as st

from runtime.record import PrimitiveType, Record
from runtime.terranode_adapter import TerraNodeRuntimeAdapter
from runtime.verifier import Verifier


json_scalar = st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=20))
json_value = st.recursive(
    json_scalar,
    lambda children: st.one_of(
        st.lists(children, max_size=4),
        st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=4),
    ),
    max_leaves=12,
)


class FuzzMalformedInputsTests(unittest.TestCase):
    @settings(max_examples=120, deadline=None)
    @given(
        envelope=st.dictionaries(
            st.text(min_size=1, max_size=12),
            json_value,
            max_size=10,
        )
    )
    def test_malformed_envelope_never_crashes_adapter(self, envelope: dict) -> None:
        adapter = TerraNodeRuntimeAdapter()
        try:
            result = adapter.submit_envelope(envelope)
            self.assertIsInstance(result.accepted, bool)
            self.assertIsNotNone(result.verification)
        except Exception as exc:
            self.assertIsInstance(exc, ValueError)

    @settings(max_examples=120, deadline=None)
    @given(
        primitive=st.sampled_from(list(PrimitiveType)),
        payload=st.dictionaries(st.text(min_size=1, max_size=8), json_value, max_size=6),
    )
    def test_random_payload_for_declared_primitive_never_crashes_verifier(
        self, primitive: PrimitiveType, payload: dict
    ) -> None:
        verifier = Verifier(
            TerraNodeRuntimeAdapter().store, allow_insecure_signatures=True, enforce_canonical_record_id=False
        )
        record = Record(
            id=f"fuzz-{primitive.value}-{hash(str(payload))}",
            type=primitive,
            author="fuzz",
            timestamp=datetime.now(timezone.utc),
            schema={
                PrimitiveType.OBSERVATION: "trs.observation.v1",
                PrimitiveType.COMMITMENT: "trs.commitment.v1",
                PrimitiveType.INTENTION: "trs.intention.v1",
            }[primitive],
            payload=payload,
            signature="sig:fuzz",
        )
        result = verifier.verify(record)
        self.assertIsInstance(result.valid, bool)
        self.assertIsInstance(result.errors, list)


if __name__ == "__main__":
    unittest.main()
