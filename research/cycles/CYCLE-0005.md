# CYCLE-0005 — TerraNode Program 3 Policy Independence

## Depends on

- CYCLE-0004 complete.

## New question

Can policy modules vary without adapter/runtime rewrites?

## Evidence targets

- Multiple policy implementations satisfy `AllocationPolicy`.
- Same adapter workflow supports all policies.

## Amendment trigger

If runtime changes are required per-policy to preserve correctness.
