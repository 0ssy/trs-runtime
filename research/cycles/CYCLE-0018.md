# CYCLE-0018 — TerraNode Program 9.11 Selective Disclosure / Privacy-Preserving Identity

## Status

Open.

## Depends on

- CYCLE-0017 complete.

## New question

Can identity-related claims be proven with selective disclosure while preserving TRS replay/audit guarantees?

## Entry criteria

- Priority use-cases for selective disclosure are defined.
- Privacy threat model is documented.

## Evidence targets

- Proof flow design and implementation artifacts.
- Tests showing required-claim proofs with minimized disclosure.
- Privacy/security review outcomes.

## Pass criteria

- Required claims are verifiable without exposing non-required identity data.
- Replay/audit properties remain intact for authorized observers.

## Fail conditions

- Proof flows require over-disclosure for core scenarios.

## Amendment trigger

Open amendment candidate only if selective disclosure is impossible under current TRS semantics for required scenarios.
