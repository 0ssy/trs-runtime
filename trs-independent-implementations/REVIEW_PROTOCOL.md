# Gate 1 Review Protocol (Clean Promotion)

Use this protocol to promote a technical-port package to a Gate 1-qualified implementation.

## Scope

Target folders:

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

## Reviewer requirements

Reviewer must be independent from the original technical-port authoring session.

## Required package contents

Each implementation folder must contain:

- `metadata.json`
- `README.md`
- `src/`
- `implementation-report.md`
- `ambiguity-report.md`
- `independence-attestation.md`
- `evidence/`

## Promotion checklist (all required)

1. **Conformance**
   - Run implementation-specific conformance execution.
   - Save output under `evidence/`.
   - Set `conformance_status` to `pass` only if all required vectors pass.

2. **Interoperability**
   - Run interoperability checks against the reference runtime/network contract.
   - Save output under `evidence/`.
   - Set `interoperability_status` to `pass` only on successful sync/replay checks.

3. **Ambiguity report**
   - Update `ambiguity-report.md` with all implementation-affecting ambiguities and chosen interpretations.
   - Set `ambiguity_report_status` to `pass` only when report is complete and reviewed.

4. **Independence attestation**
   - Update `independence-attestation.md` with reviewer identity/date and explicit spec-only semantic source statement.
   - Set `independence_attestation_status` to `pass` only after independent review sign-off.

5. **Metadata evidence paths**
   - Ensure `metadata.json` includes all concrete evidence file paths under `evidence_paths`.
   - All paths listed in `evidence_paths` must exist.

## Aggregate verification command

Run from repository root:

```bash
venv\Scripts\python.exe research\interop\run_gate1_independent_impls_status.py status
```

Qualification rule is strict: an implementation is counted only when all four statuses are `pass` and required files/evidence paths are present.
