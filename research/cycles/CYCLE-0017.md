# CYCLE-0017 — TerraNode Program 9.10 SDKs and Third-Party Onboarding

## Status

In progress (Python SDK baseline started; multi-language and external onboarding pending).

## Depends on

- CYCLE-0016 complete.

## New question

Can external teams integrate with TRS/TerraNode without insider assistance?

## Entry criteria

- SDK language targets selected and maintained.
- Onboarding docs baseline drafted from outsider perspective.

## Evidence targets

- SDK release artifacts and examples.
- Third-party onboarding trial logs.
- External conformance outcomes.

## Baseline initialized

- Harness: `research/sdk/run_cycle_0017_sdk_baseline.py`
- Latest summary: `evidence/sdk/cycle0017_latest.json`
- Timestamped artifact: `evidence/sdk/2026-08-04T071332Z_cycle0017_sdk_baseline.json`
- Initial Python SDK surface:
  - `terranode/terranode/sdk/python_client.py`
  - `terranode/tests/test_program9_10_sdk.py`

### Current baseline result

- Python SDK integration baseline: pass
- Additional SDK language implementations and third-party onboarding: pending for closure

## Pass criteria

- Independent teams complete integration + basic conformance unaided by original authors.
- SDK interfaces remain stable across supported workflows.

## Fail conditions

- Third-party integration requires tribal knowledge or direct author intervention.

## Amendment trigger

Only if repeated onboarding failures indicate spec-level ambiguity requiring TRS clarification/amendment.
