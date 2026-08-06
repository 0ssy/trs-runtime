# CYCLE-0020 — TerraNode Program 10 Human Coordination Validation

## Status

In progress — study package implemented; real-participant validation pending.

## Depends on

- Gate 1 through Gate 6 complete.
- CYCLE-0019 completed.

## New question

Do users resolve coordination disputes faster and more accurately with TerraNode-style timeline/replay/evidence/authority/conflict/explanation views than with ordinary status/activity/comment views?

## Scenario

Alice creates task -> Bob authorized -> Bob offline -> Bob claims completed -> Alice claims incomplete -> reconnect -> conflict.

## Study package

- Program assets: `terranode-program10/`
- Generator: `terranode-program10/app/run_program10.py`
- Participant entrypoint: `terranode-program10/START_HERE.md`
- Core module: `terranode/terranode/program10_human_coordination.py`
- Validation test: `terranode/tests/test_program10_human_coordination_validation.py`

## Evidence artifacts

- Scenario: `terranode-program10/scenarios/alice_bob_offline_conflict.json`
- Ordinary interface: `terranode-program10/comparison/ordinary_logs/`
- TerraNode interface: `terranode-program10/comparison/terranode/`
- Questionnaire: `terranode-program10/evaluation/questionnaire.md`
- Metrics: `terranode-program10/evaluation/metrics.csv`
- Observations: `terranode-program10/evaluation/observations.md`
- Participants: `terranode-program10/participants/participants.csv`
- Session index: `terranode-program10/recordings/session_index.md`
- Final report: `terranode-program10/report.md`
- Real-study runbook: `terranode-program10/evaluation/REAL_STUDY_RUNBOOK.md`

## Result summary

- Synthetic baseline rows generated: 6 participant profiles (scaffold only, not real sessions)
- Baseline means from scaffold: ordinary `0.64`, TerraNode `0.94`
- Validation status: real participant sessions and measured outcomes still required

## Pass criteria check

- Faster than logs: pending real-participant execution
- More accurate than logs: pending real-participant execution
- Fewer help requests: pending real-participant execution
- Users trust explanation: pending real-participant execution

## Amendment trigger

No TRS semantic contradiction observed. Improvements tracked at TerraNode UI/replay presentation layer only.
