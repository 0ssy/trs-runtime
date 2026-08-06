# CYCLE-0012 Interop Baseline Harness

Run from repository root:

```bash
venv\Scripts\python.exe research\interop\run_cycle_0012_baseline.py
venv\Scripts\python.exe research\interop\run_cycle_0012_cross_impl.py
venv\Scripts\python.exe research\interop\run_cycle_0012_sdk_cross_runtime.py
venv\Scripts\python.exe research\interop\run_gate1_independent_impls_status.py status
```

Outputs:

- `evidence/interop/<timestamp>_cycle0012_fixture.json`
- `evidence/interop/<timestamp>_cycle0012_summary.json`
- `evidence/interop/cycle0012_latest.json`
- `evidence/interop/<timestamp>_cycle0012_cross_impl_summary.json`
- `evidence/interop/cycle0012_cross_latest.json`
- `evidence/interop/<timestamp>_cycle0012_rust_sdk_flow.json`
- `evidence/interop/<timestamp>_cycle0012_java_sdk_flow.json`
- `evidence/interop/<timestamp>_cycle0012_sdk_cross_runtime_summary.json`
- `evidence/interop/cycle0012_sdk_cross_runtime_latest.json`
- `evidence/interop/<timestamp>_gate1_independent_impls_status.json`
- `evidence/interop/gate1_independent_impls_latest.json`
