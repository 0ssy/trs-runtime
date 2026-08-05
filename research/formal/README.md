# CYCLE-0013 Mechanized Verification Harness

Run from repository root:

```bash
venv\Scripts\python.exe research\formal\run_cycle_0013_model_check.py
venv\Scripts\python.exe research\formal\run_cycle_0013_tlc.py --tlc-jar %TEMP%\tla2tools.jar
```

Outputs:

- `evidence/formal/<timestamp>_cycle0013_model_check.json`
- `evidence/formal/cycle0013_latest.json`
- `evidence/formal/<timestamp>_cycle0013_tlc.json`
- `evidence/formal/cycle0013_tlc_latest.json`
- `evidence/formal/tlc/<timestamp>_cycle0013_tlc.log`

The harness explores a bounded two-node append/sync state-space and checks:

- append-only growth,
- causal and authorization closure,
- non-silent conflict visibility,
- replay equivalence at equal inventories,
- terminal convergence and closure.
