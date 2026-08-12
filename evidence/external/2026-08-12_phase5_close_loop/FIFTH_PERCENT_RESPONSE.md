# Fifth Percent follow-up (evidence update)

This is the evidence-backed delta since your findings, not a status update.

## 1) Unauthorized commitment acceptance path closed

- Change: commitments without authorization now fail Rule 6.1.
- Runtime: `runtime/verifier.py::verify_authorization`
- Regression locks:
  - `tests/test_verifier.py::test_commitment_without_authorization_fails`
  - `conformance/capability/test_reported_authorization_regressions.py`

## 2) Rootless trust-root pattern closed

- Change: trust root is explicit self-authorization + signature verification, not "no causes/no auth" pattern.
- Runtime: `runtime/verifier.py::_is_self_authorized_root`
- Regression locks:
  - `tests/test_verifier.py::test_rootless_record_is_not_trust_root`
  - `conformance/capability/test_reported_authorization_regressions.py`

## 3) Canonical/content-derived identity amendment landed

- Amendment: `TRS-0003` (accepted) in `docs/Amendment_Log.md`
- Runtime:
  - `runtime/canonical.py::derive_record_id`
  - `runtime/record.py::Record.create`

## 4) Full validation evidence refreshed

- Full suite pass (fresh timestamp):
  - `evidence/test_runs/2026-08-12T081400Z_validation_cycle.log`
- Attack suite summary inside cycle: `10/10 blocked`
- Benchmark gate artifact:
  - `benchmarks/history/2026-08-12T081408Z_records-120_median-of-2.json`
