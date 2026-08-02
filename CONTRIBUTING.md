# Contributing / Source-of-Truth Workflow

## Canonical source

- The canonical source of truth is `origin/main`:
  - `https://github.com/0ssy/trs-runtime`
- Zip files are for distribution only, never for canonical merge decisions.

## Required start-of-session sync

Before any edit, every environment/agent must run:

```bash
git fetch --prune origin
git switch main
git pull --ff-only origin main
```

## Required pre-push verification

Every push to `main` must be based on executed commands, not summaries:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m unittest discover -s conformance -p "test_*.py" -v
python attacks/run_attacks.py
```

If the change affects evidence/perf pipeline, also run:

```bash
python experiments/0006-validation/run_validation_cycle.py --gate-mode nightly --allow-benchmark-regressions
```

## Multi-agent coordination rules

- Both agent threads must work against the same remote (`origin/main`).
- No "done" claim without command output.
- If two threads touch the same scope, one must pause until the other push is fetched and integrated.
- Resolve drift by `git diff origin/main...HEAD`, not by comparing narrative summaries.
