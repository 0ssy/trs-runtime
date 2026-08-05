# trs-conformance

Implementation-neutral TRS conformance vectors and expected behavior.

This package intentionally contains:

- JSON input vectors
- expected outcomes
- runner contract documentation

This package intentionally does **not** contain:

- reference-runtime implementation code
- language-specific test harness code

## Layout

- `vectors/valid/`: records that must verify successfully.
- `vectors/invalid/`: records that must fail with specific rule evidence.
- `vectors/replay/`: replay-state reconstruction vectors.
- `vectors/authorization/`: authorization traceability vectors.
- `expected/`: expected outcomes keyed by vector id.
- `runner-spec.md`: standard runner inputs/outputs.
- `interop-matrix.md`: cross-implementation interoperability checks.

## Goal

Any TRS implementation should be able to consume these vectors and produce equivalent outcomes without depending on this repository's runtime code.
