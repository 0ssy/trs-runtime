# TRS Documentation

<div style="background:#ffebaf;padding:12px;border-left:6px solid #4c9db0;">
<strong>Why TRS?</strong><br/>
TRS is an append-only coordination runtime for distributed systems that need verifiable history, explicit conflict visibility, and clean separation between coordination infrastructure and application business logic.
</div>

## What problem TRS solves

TRS solves coordination in environments where:

- multiple actors make concurrent claims or commitments,
- network connectivity may be intermittent,
- auditability and replayability matter,
- no central authority can be trusted to silently rewrite history.

## Why append-only coordination is different

- Every decision is a record, never an in-place overwrite.
- Conflicts become visible records, not hidden state loss.
- Replay can reconstruct derived state deterministically.

## Why three primitives are enough

TRS uses only:

- `Observation`
- `Commitment`
- `Intention`

Domain complexity stays in payloads, schemas, and policies above the runtime, while the kernel remains stable.

## What TRS guarantees (and does not)

### Guarantees

- Immutable append-only records
- Causal traceability
- Explicit conflict visibility
- Verifier-driven structural correctness per declared primitive

### Deliberately out of scope

- Allocation policy choices
- App-specific workflow semantics
- User identity UX and account systems
- Product/business logic

## Learning path

1. [What is TRS?](getting-started/01-what-is-trs.md)
2. [Why was it created?](getting-started/02-why-trs.md)
3. [Core concepts](getting-started/03-core-concepts.md)
4. [Build your first application](tutorials/01-first-application.md)
5. [Run your first node](node/README.md)
6. [Use the Python SDK](sdk/README.md)
7. [Use the CLI](cli/README.md)
8. [Read the specification](specification/README.md)
9. [Read the Design Record](design-record/README.md)

## Repository structure

```
trs-docs/
├── docs/
├── getting-started/
├── tutorials/
├── specification/
├── runtime/
├── node/
├── sdk/
├── cli/
├── examples/
├── conformance/
├── amendments/
├── design-record/
└── README.md
```

