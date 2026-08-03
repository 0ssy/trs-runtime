# TerraNode Program 1 — Consumer Validation

## Objective

Demonstrate resource-scarcity coordination by consuming frozen TRS runtime interfaces without modifying TRS core modules.

## Scope

- `terranode/runtime_adapter.py`: only TerraNode module importing TRS runtime.
- `terranode/policy.py`: pure allocation policy over `ConflictSet`.
- `terranode/main.py`: single scarcity demonstration.

## Scenario

- Subject: `warehouse-7`
- Available: `100`
- Claims: Alice `80`, Bob `60`
- Policy: Pro-rata allocation
- Expected grants: Alice `57.14`, Bob `42.86`

## Gate Statement

Program 1 is considered successful only if all tests pass and no TRS-RR runtime code changes are required for TerraNode execution.
