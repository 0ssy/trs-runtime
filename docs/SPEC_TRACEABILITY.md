| TRS Rule                       | Runtime Module                         | Conformance Test                                      | Attack Record |
| ------------------------------ | -------------------------------------- | ----------------------------------------------------- | ------------- |
| 4.1 Immutability               | `verifier.py::verify_immutability`     | `conformance/semantics/test_immutability.py`          | `ATTACK-001_duplicate-id.md` |
| 4.2 Causality                  | `verifier.py::verify_causality`        | `conformance/workflow/test_genesis.py`                | `ATTACK-003_cycle-creation.md`, `ATTACK-012_partition-reconnection-sync.md` |
| 4.3 Local Sufficiency          | `verifier.py::verify_local_sufficiency`| `conformance/identity/test_local_query.py`            | `ATTACK-009_query-mutation.md`, `ATTACK-012_partition-reconnection-sync.md` |
| 4.4 Closure                    | `verifier.py::verify_closure`          | `conformance/workflow/test_intention_completion.py`   | `ATTACK-003_cycle-creation.md` |
| 4.5 Non-Silent Conflict        | `graph.py` + `query.py`                | `conformance/conflict/test_conflict_visibility.py`    | `ATTACK-010_hidden-conflict.md` |
| 5.1 Schema Declaration         | `verifier.py::verify_schema`           | `conformance/contracts/test_contract_schema.py`       | `ATTACK-004_schema-mismatch.md` |
| 5.2 Signature Presence         | `verifier.py::verify_signature`        | `conformance/semantics/test_immutability.py`          | `ATTACK-006_invalid-genesis.md` |
| 5.3 Payload Shape              | `verifier.py::verify_payload_shape`    | `tests/test_verifier.py`                              | `ATTACK-008_payload-sniffing.md`, `ATTACK-011_malformed-envelope-fuzz.md` |
| 6.1 Authorization Traceability | `verifier.py::verify_authorization`    | `conformance/capability/test_capability_forgery.py`   | `ATTACK-002_forged-authority.md` |

## Integration Boundary

| Separation Requirement                            | Runtime Module                 | Test                            |
| ------------------------------------------------- | ------------------------------ | ------------------------------- |
| TerraNode consumes runtime, does not embed axioms | `runtime/terranode_adapter.py` | `tests/test_terranode_adapter.py` |
