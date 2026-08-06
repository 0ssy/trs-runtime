# Program 10 Real Study Runbook

## Purpose

Convert the current synthetic baseline into real participant evidence for CYCLE-0020 closure.

## Minimum completion criteria

- At least 5 real participants complete the study.
- Each participant uses both interfaces for the same scenario.
- Questionnaire answers are recorded without hints.
- Time, accuracy, confidence, and help-request metrics are captured.
- Feedback is submitted in public repo channels.

## Session procedure (per participant)

1. Share `terranode-program10/START_HERE.md`.
2. Ask participant to run:
   - `python terranode-program10/app/run_program10.py`
3. Ask participant to review:
   - `terranode-program10/comparison/ordinary_logs/`
   - `terranode-program10/comparison/terranode/`
   - `terranode-program10/comparison/index.html`
4. Ask participant to answer `terranode-program10/evaluation/questionnaire.md` without hints.
5. Record metrics in `terranode-program10/evaluation/metrics.csv`.
6. Record participant profile and completion in `terranode-program10/participants/participants.csv`.
7. Add session recording reference in `terranode-program10/recordings/session_index.md`.
8. Ask participant to submit public feedback:
   - GitHub Issues: bugs and feature suggestions.
   - GitHub Discussions (if enabled): broader opinions and design discussion.

## Data integrity rules

- Replace `synthetic_baseline` rows with real-session rows.
- Keep synthetic rows only if clearly separated and labeled.
- Do not overwrite session history without preserving provenance.

## Finalization checklist

- Update `terranode-program10/report.md` with real metrics summary.
- Update `research/cycles/CYCLE-0020.md` status and pass criteria.
- Update `research/RESULTS_LEDGER.md` CYCLE-0020 outcome from in-progress to closed only after real data is complete.
