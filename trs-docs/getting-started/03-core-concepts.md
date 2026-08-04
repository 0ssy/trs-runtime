# Core concepts

## Record envelope

Records include stable metadata (`id`, `type`, `author`, `timestamp`, `schema`) and immutable payload content with causal/authorization links.

## Verifier

Rule-based checks enforce:

- immutability,
- causality,
- closure,
- non-silent conflict visibility,
- authorization traceability,
- schema and payload-shape validity,
- signature presence/verification.

## Replay

Replay reconstructs derived state from immutable history, producing deterministic results for the same record set.

