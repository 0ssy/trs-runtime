# trs-independent-implementations

Collection point for independent implementation evidence.

Tracks:

- implementation reports,
- ambiguity reports,
- discovered assumptions,
- interoperability run results.

Folders:

- `reports/`
- `ambiguities/`
- `assumptions/`
- `interop-results/`
- `implementations/` (one package per implementation)

## Technical-port review set

This repository now includes the ten-slot technical-port review set under:

- `implementations/impl-0001-independent-python`
- `implementations/impl-0002-rust`
- `implementations/impl-0003-java`
- `implementations/impl-0004-go`
- `implementations/impl-0005-csharp`
- `implementations/impl-0006-typescript`
- `implementations/impl-0007-kotlin`
- `implementations/impl-0008-swift`
- `implementations/impl-0009-cpp`
- `implementations/impl-0010-ruby`

Aggregate technical review artifacts:

- `TECHNICAL_PORTS.md`
- `TECHNICAL_PORTS_VALIDATION.json`
- `TECHNICAL_GATE1_STATUS.json`
- `REVIEW_PROTOCOL.md`
- `REVIEWER_CHECKLIST.md`

## Gate 1 status command

Generate measured Gate 1 status evidence:

```bash
venv\Scripts\python.exe research\interop\run_gate1_independent_impls_status.py status
```

An implementation counts toward Gate 1 only when all four metadata statuses are `pass`:

- `conformance_status`
- `interoperability_status`
- `ambiguity_report_status`
- `independence_attestation_status`

Use `REVIEW_PROTOCOL.md` for the step-by-step promotion process.
