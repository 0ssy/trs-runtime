# CYCLE-0016 Red-Team Campaign Scope (Baseline)

## Objective

Stress multi-node synchronization and verification behavior under adversarial input at campaign scale.

## Baseline campaign phases

1. Start multi-node topology with shared valid history.
2. Inject forged/malformed record into attacker node out-of-band.
3. Execute bidirectional sync rounds across the mesh.
4. Confirm malicious record rejection by honest nodes.
5. Run attack suite for known exploit classes.
6. Capture campaign telemetry and outcomes in evidence artifacts.

## Rules of engagement (baseline)

- No destructive operations against host environment.
- No data deletion or mutable history rewriting.
- All adversarial records are synthetic and isolated to test stores.

## Pending external phase

This baseline is internal simulation only. Independent external red-team execution remains required for cycle closure.
