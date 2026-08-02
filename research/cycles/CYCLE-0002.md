# CYCLE-0002 — Next Research Plan (Programs 5–10)

## Objective

Execute the next research phase as experimentation, not feature expansion.

## Runtime freeze rule

No change to `runtime/` unless:

1. A reproducible experiment shows implementation violation of frozen TRS semantics, or
2. An approved amendment (TRS-000x) requires it.

## Programs

### Program 5 — Scale

```bash
python experiments/0007-scale/run_scale_campaign.py --records 10000 100000
```

### Program 6 — Byzantine behavior

```bash
python experiments/0008-byzantine/run_byzantine_campaign.py
```

### Program 7 — Implementation independence (cross-backend agreement fixture)

```bash
python experiments/0009-implementation-independence/run_implementation_independence.py
```

### Program 8 — Formalization checks

```bash
python experiments/0010-formalization/run_formalization_checks.py
```

### Program 9 — Tiny reference applications above TRS

```bash
python experiments/0011-reference-apps/run_reference_apps.py
```

### Program 10 — Independent attack handoff packet

```bash
python experiments/0012-independent-attack/run_independent_attack_packet.py
```

## One-command cycle runner

```bash
python experiments/0013-cycle-0002/run_cycle_0002.py --scale-records 10000 100000
```

## Decision outputs

Each program should be classified as one of:

- `TRS survives`
- `TRS refined`
- `TRS broken`
- `NEED_MORE_EVIDENCE`

## Current results (provisional close)

- Program 5 (Scale): `TRS survives`
  - Executed at 10k, 20k, 30k across in-memory, SQLite, LMDB, RocksDB.
  - Scale evidence collected in `evidence/experiments/program5_scale_latest.json`.
- Program 6 (Byzantine): `TRS survives`
- Program 7 (Implementation Independence): `TRS survives`
- Program 8 (Formalization): `TRS survives`
- Program 9 (Reference Apps): `TRS survives`
- Program 10 (Independent Attack): `NEED_MORE_EVIDENCE`
  - Internal submission completed: `research/cycles/CYCLE-0002_INDEPENDENT_ATTACK_SUBMISSION.md`
  - Internal run survived (attacks blocked, fuzz passed, byzantine campaign survived).
  - External/independent evaluator run still pending for final closure.

## Amendment decision

`TRS-0002` not triggered by CYCLE-0002 evidence to date.
