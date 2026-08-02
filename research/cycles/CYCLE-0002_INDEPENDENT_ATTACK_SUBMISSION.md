# CYCLE-0002 Independent Attack Submission

## Evaluator

- Name / Handle: josep (internal execution)
- Date: 2026-08-02
- Machine / OS: Windows / PowerShell
- Repository commit/tag: local working tree

## Objective

Attempt to break TRS runtime behavior (not improve it).

## Commands executed

```text
python attacks/run_attacks.py
python -m unittest -v tests.test_fuzz_malformed_inputs
python experiments/0008-byzantine/run_byzantine_campaign.py
python experiments/0006-validation/run_validation_cycle.py --gate-mode nightly
```

## Findings

1. Attempt ID: P10-A1
2. Attack description: Execute baseline attack catalog
3. Expected break condition: Any attack accepted as valid
4. Actual result: 10/10 attacks blocked
5. Classification: blocked
6. Evidence file paths: `evidence/experiments/program10_attacks.log`
7. Reproduction steps: rerun command set above

1. Attempt ID: P10-A2
2. Attack description: Fuzz malformed envelopes/payloads
3. Expected break condition: crash or malformed acceptance
4. Actual result: test suite passed (2/2)
5. Classification: blocked
6. Evidence file paths: `evidence/experiments/program10_fuzz.log`
7. Reproduction steps: rerun command set above

1. Attempt ID: P10-A3
2. Attack description: Byzantine campaign execution
3. Expected break condition: divergence or invalid acceptance
4. Actual result: byzantine artifact generated; scenario outcome survives
5. Classification: blocked
6. Evidence file paths: `evidence/experiments/program10_byzantine.log`, `evidence/experiments/program6_byzantine_latest.json`
7. Reproduction steps: rerun command set above

1. Attempt ID: P10-A4
2. Attack description: Full validation cycle under nightly gate
3. Expected break condition: semantic verifier break
4. Actual result: failed only at benchmark gate; no semantic break evidence
5. Classification: partial
6. Evidence file paths: `evidence/experiments/program10_validation_cycle.log`, `evidence/test_runs/2026-08-02T095328Z_validation_cycle.log`
7. Reproduction steps: rerun command set above

## Breach proof (if any)

- Minimal reproducible steps: none found
- Why this violates TRS semantics: not applicable
- Proposed rule mapping (e.g., 4.1 / 4.2 / 6.1): not applicable

## TRS-0002 candidate statement

No TRS-0002 candidate from this submission.

## Final evaluator decision

`TRS survives` (internal run), with benchmark-gate instability remaining performance/evidence noise rather than semantic breach.
