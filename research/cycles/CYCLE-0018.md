# CYCLE-0018 — TerraNode Program 9.11 Selective Disclosure / Privacy-Preserving Identity

## Status

In progress (selective-disclosure baseline started; advanced ZK/VC layer pending).

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

## Baseline initialized

- Harness: `research/privacy/run_cycle_0018_privacy_baseline.py`
- Latest summary: `evidence/privacy/cycle0018_latest.json`
- Timestamped artifact: `evidence/privacy/2026-08-04T071332Z_cycle0018_privacy_baseline.json`
- Initial privacy module:
  - `terranode/terranode/privacy.py`
  - `terranode/tests/test_program9_11_privacy.py`

### Current baseline result

- Selective-disclosure baseline test: pass
- ZK-grade proof systems and external privacy review: pending for closure

## Pass criteria

- Required claims are verifiable without exposing non-required identity data.
- Replay/audit properties remain intact for authorized observers.

## Fail conditions

- Proof flows require over-disclosure for core scenarios.

## Amendment trigger

Open amendment candidate only if selective disclosure is impossible under current TRS semantics for required scenarios.
