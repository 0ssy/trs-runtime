# Implementation Report — impl-0001-independent-python

## Implementation summary

This package is an independent Python implementation of the TRS v1.0 record graph. It implements append-only local storage, structural envelope validation, causal and authorization-reference checks, subject-scoped conflict visibility, unordered import, and replay projections for intention closure and intention-to-commitment links. Payload values are retained as opaque JSON objects; the implementation does not evaluate domain semantics.

The implementation was derived from the normative artifacts `docs/TRS_v1.0.pdf`, `docs/Design_Record.pdf`, and `docs/Amendment_Log.md`. It does not import, subclass, call, or reference the repository runtime package for semantic behavior. The repository’s independent interoperability harness was used only as an external test fixture and comparison surface.

## Outcomes

| Check | Outcome | Evidence |
|---|---|---|
| Conformance vectors | Pass: all valid, invalid, replay, and authorization vectors | `evidence/conformance-results.json`, `evidence/conformance-run.log` |
| Interoperability | Pass: 8/8 records imported, no rejections, inventory hash matched, conflict remained visible | `evidence/interop-results.json`, `evidence/interop-run.log`, `evidence/cross-interop-run.log` |
| Ambiguity report | Pass: all implementation-affecting ambiguities and assumptions are recorded | `ambiguity-report.md` |
| Independence attestation | Fail / pending external review: spec-only statement exists, but separate-team authorship is not established | `independence-attestation.md` |

## Technical-test qualification boundary

This package’s conformance and interoperability results remain useful as technical evidence. However, under the user-selected ten-port technical-test mode, it is not counted as an independently authored Gate 1 implementation until a distinct contributor reviews and signs the attestation.

## Contradiction notes

The contributor instruction names `docs/DesignRecord.pdf` or `.md`, while the supplied repository contains `docs/Design_Record.pdf` with an underscore. The latter was used as the available Design Record artifact. The baseline script likewise looks for the hyphenated `DesignRecord.pdf`, so its frozen-document hash output reports that candidate as missing even though the underscore-named Design Record exists. This is a repository naming inconsistency, not a runtime semantic change.

The conformance fixtures represent genesis records with an empty `causes` array but do not carry an explicit `genesis` envelope field. The implementation accepts an empty-cause record as the fixture’s genesis form and records that assumption in the ambiguity report. This is necessary to execute the supplied normative test vectors and is not treated as an authorization grant for non-genesis records.

The fixture schema uses primitive-specific payload keys (`subject`/`value`, `action`/`due_by`, and `goal`/`horizon`) and expected error strings for payload-shape validation. The implementation validates those structural fixture requirements while keeping all payload values opaque and semantically uninterpreted.

## References

[1]: ../../../../docs/TRS_v1.0.pdf "TRS v1.0 normative specification"
[2]: ../../../../docs/Design_Record.pdf "TRS Design Record"
[3]: ../../../../docs/Amendment_Log.md "TRS Amendment Log"
