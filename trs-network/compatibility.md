# Compatibility Rules

## Runtime vs network

- TRS runtime semantics are independent from transport.
- Network/auth/deployment concerns must not alter core verifier rules.

## Backward compatibility guarantees

- Existing required fields keep identical meaning across patch/minor revisions.
- New optional fields may be added without breaking old clients.
- Removal or semantic redefinition of existing required fields requires major protocol bump.

## Interop expectation

Any implementation passing `trs-conformance` vectors and speaking `TRS-NET-1` should interoperate for submit/query/sync/replay flows.
