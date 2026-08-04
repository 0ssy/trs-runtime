# Pre-Pilot External Handoff (Programs 9.5, 9.7, 9.8, 9.9)

This handoff package defines what external parties need to execute before pilot eligibility.

## Scope

- 9.5 Independent second implementation interop
- 9.7 Production crypto + external security audit
- 9.8 Amendment governance adoption
- 9.9 Live distributed red-team campaign

## Build/verify handoff pack

From repository root:

```bash
venv\Scripts\python.exe research\handoff\build_external_handoff_pack.py
```

Artifacts:

- `evidence/handoff/<timestamp>_pre_pilot_external_handoff.json`
- `evidence/handoff/pre_pilot_external_handoff_latest.json`

## External execution responsibilities

### 9.5 Independent implementation team

- Build second runtime from frozen TRS docs only.
- Execute cross-implementation interop using provided fixture flow.
- Submit interoperability logs and divergence report.

### 9.7 Security auditors

- Execute independent audit per scope and threat model.
- Provide severity-ranked report with reproducible findings.
- Confirm remediation retest outcomes.

### 9.8 Governance participants

- Adopt charter roles and run amendment process with real participants.
- Produce signed ratification trace and state transitions.

### 9.9 Red-team operators

- Run live multi-node adversarial campaign.
- Provide exploit attempts, findings, mitigations, and retest logs.
