# TRS Research Execution Matrix (v1.0 Freeze)

This matrix operationalizes the PDF methodology:

- Freeze Sections 1–9 of TRS v1.0.
- Attack and validate implementation behavior.
- Convert contradictions into amendment proposals (not ad-hoc runtime expansion).

## Decision rule

Every campaign ends in exactly one of:

1. **TRS survives** (confidence increases), or
2. **TRS-0002 candidate** (contradiction or insufficiency evidenced).

No third outcome.

## Program 1 — Implementation Validation

Goal: falsify runtime correctness under adversarial and edge-case conditions.

| Campaign | Primary Mechanism | Pass Condition | TRS-0002 Trigger |
| --- | --- | --- | --- |
| Attack replay | `python attacks/run_attacks.py` | All attacks blocked; no silent conflict | Accepted forged/unauthorized/hidden-conflict path |
| Generated invariants | `python -m unittest -v tests.test_property_invariants` | All invariants pass | Counterexample violating immutability, explainability, or query-state separation |
| Malformed/fuzz inputs | `python -m unittest -v tests.test_fuzz_malformed_inputs` | No crash + malformed records rejected | Runtime accepts malformed envelope/payload or verifier crashes |
| Mutation pressure | `python -m unittest -v tests.test_mutation_checks` | All defined mutants killed | Mutant survives (safety rule not actually enforced) |
| Multi-node partition/rejoin | `python -m unittest -v tests.test_multi_node_sim` and `python experiments/0005-multi-node/run_multi_node_sim.py` | Eventual convergence + invalid records rejected by peers | Divergence, invalid acceptance, or state corruption after reconnection |

## Program 2 — Performance Validation

Goal: verify TRS behavior remains acceptable under realistic load and storage backends.

| Campaign | Primary Mechanism | Pass Condition | TRS-0002 Trigger |
| --- | --- | --- | --- |
| Baseline capture | `python benchmarks/rebaseline_benchmarks.py --mode nightly --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json` | Baseline artifact captured + prior baseline archived | Baseline cannot be captured deterministically enough for governance |
| PR gate | `python benchmarks/gate_benchmarks.py --mode pr --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json` | No regression beyond PR thresholds | Persistent regressions in common paths across runs |
| Nightly strict gate | `python benchmarks/gate_benchmarks.py --mode nightly --baseline evidence/benchmarks/2026-08-01_phase15_baseline.json` | No regression beyond strict thresholds (with explicit jitter overrides) | Persistent strict-mode failures after rebaseline on stable host |
| Full validation cycle | `python experiments/0006-validation/run_validation_cycle.py --gate-mode nightly` | All validation steps pass | Functional pass but irreducible nightly perf failure tied to core semantics |

## Program 3 — Formal/Invariant Validation

Goal: raise confidence in spec-level invariants as mathematical constraints.

| Campaign | Current Mechanism | Near-Term Expansion | TRS-0002 Trigger |
| --- | --- | --- | --- |
| Property-based verification | Hypothesis invariants in `tests/test_property_invariants.py` | Increase graph topology depth and authorization chain complexity | Repeatable invariant break under valid envelope construction |
| Adversarial structure fuzzing | Fuzz tests in `tests/test_fuzz_malformed_inputs.py` | Add corpus-guided payload/schema boundary fuzzing | Structural acceptance of invalid records |
| Mutation robustness | `runtime/mutation_checks.py` + `tests/test_mutation_checks.py` | Add mutants around sync/replay/crypto invariants | Surviving mutant in normative rule path |

## Program 4 — First Consumer Proof (TerraNode)

Goal: prove a complete application can remain above TRS without changing TRS core.

| Campaign | Boundary Rule | Pass Condition | TRS-0002 Trigger |
| --- | --- | --- | --- |
| Adapter-only integration | TerraNode uses `runtime/terranode_adapter.py` only | No TerraNode logic requires core-runtime rule changes | TerraNode requires modifying TRS Sections 1–9 semantics |
| Domain completeness via queries | Identity/workflow/contracts/reputation/capability remain derived | All required app decisions explainable from record graph/query results | Required behavior cannot be expressed as TRS records + queries |
| Amendment discipline | Changes proposed through amendment docs, not runtime drift | Any needed change captured as explicit amendment proposal | Untraceable runtime patch added without amendment rationale |

## Governance and cadence

1. Keep `docs/TRS_v1.0.pdf` frozen.
2. Run PR policy on every PR (`--gate-mode pr`).
3. Run strict policy nightly (`--gate-mode nightly`).
4. Record evidence under `evidence/` and `benchmarks/history/`.
5. For any contradiction, open amendment proposal with:
   - failing evidence artifact(s),
   - violated rule(s),
   - minimal elevation analysis,
   - proposed normative change.

## Amendment threshold checklist

A TRS-0002 proposal is warranted only if all are true:

- Failure is reproducible across independent runs.
- Failure is not explainable by infra noise or benchmark jitter.
- Failure maps to a normative rule, not an implementation typo.
- Fix would require changing spec semantics or adding a new minimal primitive/layer.
