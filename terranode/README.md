# TerraNode Program 1

TerraNode Program 1 is a consumer-validation experiment over TRS runtime.

## Layout

- `terranode/policy.py`: pure allocation policy types and logic.
- `terranode/runtime_adapter.py`: TRS integration boundary.
- `terranode/trust.py`: trust/reputation weighting model and policy adapter.
- `terranode/authority.py`: multi-authority mediation layer.
- `terranode/semantics.py`: explicit semantic mapping registry.
- `terranode/capability.py`: consumer-side capability scope/expiry/supersession checks.
- `terranode/boundary.py`: public submission gateway with quotas and validation.
- `terranode/human.py`: offline channel queue/flush workflow.
- `terranode/network/`: distributed node, transport, and partition simulation layer.
- `terranode/sdk/`: SDK entrypoints (starting with Python).
- `terranode/privacy.py`: selective-disclosure baseline module.
- `terranode/application.py`: app-first validation backlog and first vertical slice runner.
- `terranode/identity_application.py`: identity-service vertical slice with failure and proof artifacts.
- `terranode/reputation_application.py`: reputation-service vertical slice with trust-weighted workflow artifacts.
- `terranode/workflow_application.py`: workflow-engine vertical slice with offline ingestion and convergence artifacts.
- `terranode/main.py`: scarcity demonstration flow.
- `tests/`: policy, adapter, and end-to-end tests.
- `tests/test_program10_human_coordination_validation.py`: Program 10 study package generation validation.
- `docs/ROADMAP_P2_P9.md`: dependency-ordered post-v1.0 research stack.
- `docs/PRE_PILOT_STACK_9_5_TO_9_11.md`: mandatory pre-pilot validation stack.
- `examples/scarcity_demo.py`: runnable demo entrypoint.

## Run tests

```bash
python -m unittest -v terranode.tests.test_policy
python -m unittest -v terranode.tests.test_adapter
python -m unittest -v terranode.tests.test_program1
python -m unittest -v terranode.tests.test_program2_distributed
python -m unittest -v terranode.tests.test_program2_network
python -m unittest -v terranode.tests.test_program3_policy_independence
python -m unittest -v terranode.tests.test_program4_trust_weighted
python -m unittest -v terranode.tests.test_program5_multi_authority
python -m unittest -v terranode.tests.test_program6_semantic_interoperability
python -m unittest -v terranode.tests.test_program7_capability_security
python -m unittest -v terranode.tests.test_program8_public_submission_boundary
python -m unittest -v terranode.tests.test_program9_human_systems
python -m unittest -v terranode.tests.test_program10_human_coordination_validation
python -m unittest -v terranode.tests.test_program9_10_sdk
python -m unittest -v terranode.tests.test_program9_11_privacy
python -m unittest -v terranode.tests.test_app_vertical_slice
python -m unittest -v terranode.tests.test_app_identity_vertical_slice
python -m unittest -v terranode.tests.test_app_reputation_vertical_slice
python -m unittest -v terranode.tests.test_app_workflow_vertical_slice
```

## Run demo

```bash
python terranode/examples/scarcity_demo.py
python terranode/examples/app_vertical_slice.py
python terranode/examples/identity_vertical_slice.py
python terranode/examples/reputation_vertical_slice.py
python terranode/examples/workflow_vertical_slice.py
```
