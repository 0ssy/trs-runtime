| TRS Rule                       | Runtime Module                      | Test                                      |
| ------------------------------ | ----------------------------------- | ----------------------------------------- |
| 4.1 Immutability               | `verifier.py::verify_immutability`  | `conformance/semantics/test_immutability.py` |
| 4.2 Causality                  | `verifier.py::verify_causality`     | `conformance/workflow/test_genesis.py`    |
| 4.3 Local Sufficiency          | `verifier.py::verify_local_sufficiency` | `conformance/identity/test_local_query.py` |
| 4.4 Closure                    | `verifier.py::verify_closure`       | `conformance/workflow/test_intention_completion.py` |
| 4.5 Non-Silent Conflict        | `graph.py` + `query.py`             | `conformance/conflict/test_conflict_visibility.py` |
| 6.1 Authorization Traceability | `verifier.py::verify_authorization` | `conformance/capability/test_capability_forgery.py` |

## Integration Boundary

| Separation Requirement                              | Runtime Module                              | Test                               |
| --------------------------------------------------- | ------------------------------------------- | ---------------------------------- |
| TerraNode consumes runtime, does not embed axioms   | `runtime/terranode_adapter.py`              | `tests/test_terranode_adapter.py`  |
