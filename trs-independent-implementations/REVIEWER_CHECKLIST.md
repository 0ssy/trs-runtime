# Gate 1 Reviewer Checklist (One Page)

Use this checklist when reviewing one implementation package on this laptop.

---

## 0) Pick implementation

Folder:

- `trs-independent-implementations/implementations/impl-000X-*`

Open and review in this order:

1. `metadata.json`
2. `README.md`
3. `src/`
4. `implementation-report.md`
5. `ambiguity-report.md`
6. `independence-attestation.md`
7. `evidence/`

---

## 1) Run required checks

### Python slot (impl-0001-independent-python)

From repo root:

```powershell
venv\Scripts\python.exe trs-independent-implementations\implementations\impl-0001-independent-python\run_conformance.py
venv\Scripts\python.exe trs-independent-implementations\implementations\impl-0001-independent-python\interop_check.py
```

### Global interop checks (recommended once per review session)

```powershell
venv\Scripts\python.exe research\interop\run_cycle_0012_baseline.py
venv\Scripts\python.exe research\interop\run_cycle_0012_cross_impl.py
venv\Scripts\python.exe research\interop\run_cycle_0012_sdk_cross_runtime.py
```

### Other language slots (impl-0002..impl-0010)

Run the exact commands in each package `README.md` and store output logs under that package `evidence/`.

---

## 2) Update review artifacts

In the selected implementation folder:

1. Update `implementation-report.md` with final outcomes.
2. Update `ambiguity-report.md` with any open/closed ambiguities.
3. Sign `independence-attestation.md` (name/date + spec-only statement).
4. Update `metadata.json`:
   - `conformance_status`
   - `interoperability_status`
   - `ambiguity_report_status`
   - `independence_attestation_status`
   - `evidence_paths` (must point to files that exist)

---

## 3) Recompute Gate 1 status

From repo root:

```powershell
venv\Scripts\python.exe research\interop\run_gate1_independent_impls_status.py status
```

Check:

- `evidence/interop/gate1_independent_impls_latest.json`

Gate 1 counts an implementation only when all 4 metadata statuses are `pass`.

---

## 4) Reviewer sign-off

- Reviewer name:
- Date/time:
- Implementation reviewed:
- Result (`pass`/`fail`):
- Notes:
