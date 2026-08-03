# TerraNode Pre-Pilot Validation Stack (9.5–9.11)

This stack is mandatory before any real pilot that allocates real community resources.

## Dependency chain

9.5 -> 9.6 -> 9.7 -> 9.8 -> 9.9 -> 9.10 -> 9.11

## Global rule

Each stage must end with one of:

1. TRS survives with reproducible evidence, or
2. Reproducible contradiction that triggers a TRS amendment candidate.

## Pilot release gate

No pilot may begin until all stages 9.5 through 9.11 are closed as pass with linked evidence.

---

## Program 9.5 — Independent Second Implementation

- **Question**: Is TRS portable beyond the reference implementation?
- **Pass gate**:
  - A second implementation is built from the frozen spec only.
  - Cross-implementation interoperability passes.
  - No hidden reference-runtime assumptions are required.
- **Fail trigger**:
  - Incompatibility that cannot be resolved without modifying core TRS semantics.

## Program 9.6 — Mechanized Verification

- **Question**: Are core safety properties machine-checked under concurrency?
- **Pass gate**:
  - Formal model (TLA+ or Coq) covers axioms and conflict/closure guarantees.
  - Model-check/proof artifacts are reproducible.
- **Fail trigger**:
  - Mechanized model produces counterexample violating accepted semantics.

## Program 9.7 — Production Cryptography + External Security Audit

- **Question**: Is security posture sufficient for real deployment risk?
- **Pass gate**:
  - Production Ed25519 paths and key lifecycle controls are enforced.
  - Independent external security review is completed.
  - Critical findings are remediated and re-tested.
- **Fail trigger**:
  - Unresolved critical vulnerabilities or cryptographic misuse.

## Program 9.8 — Amendment Governance

- **Question**: Is amendment authority explicitly governed, not person-bound?
- **Pass gate**:
  - Formal governance process is documented and adopted.
  - Amendment acceptance criteria and voting/ratification path are operational.
  - Audit trail for amendment decisions exists.
- **Fail trigger**:
  - Amendment outcomes depend on ad-hoc, non-repeatable personal authority.

## Program 9.9 — Live-Scale Red Team

- **Question**: Does TRS remain safe under adversarial pressure in live distributed operation?
- **Pass gate**:
  - Multi-node running deployment is attacked by an adversarial team.
  - Findings are documented, triaged, and retested after mitigations.
  - No unmitigated critical exploit remains.
- **Fail trigger**:
  - Reproducible critical exploit path with no effective mitigation.

## Program 9.10 — SDKs + Third-Party Onboarding

- **Question**: Can external teams integrate without insider knowledge?
- **Pass gate**:
  - Multi-language SDKs expose stable integration paths.
  - Third-party onboarding docs are sufficient for independent use.
  - External implementers complete onboarding and basic conformance.
- **Fail trigger**:
  - Integration requires tribal knowledge from original authors.

## Program 9.11 — Selective Disclosure / Privacy-Preserving Identity

- **Question**: Can required facts be proven without over-disclosure?
- **Pass gate**:
  - Selective disclosure workflows are implemented atop TRS identity patterns.
  - Privacy-preserving proof flow is verified by tests and threat review.
  - Disclosure minimization is demonstrable for critical use cases.
- **Fail trigger**:
  - Required claims cannot be proven without leaking non-required identity data.
