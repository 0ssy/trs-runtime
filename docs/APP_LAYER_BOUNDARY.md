# Application Layer Boundary

This document captures the recurring "app-layer boundary" question.

## Boundary definition

TRS runtime is responsible for:

- immutable record append,
- envelope and rule verification,
- replay/query/explain over the record graph.

Application layer is responsible for:

- domain semantics and business rules,
- request-path UX and latency handling,
- edge policy (authentication, quotas, abuse controls),
- side effects in operational systems.

## Practical implication

If a behavior can be expressed as **domain policy** without changing TRS primitives/rules, it belongs in the application layer (adapter/library/service).  
If a behavior requires changing TRS invariants, it must go through amendment discipline.

## Byron-style answer (canonical form)

TRS should not absorb app semantics.  
Apps should map their semantics into TRS envelopes and consume TRS outputs (replay/conflict/explain), while keeping business logic outside the core runtime.

