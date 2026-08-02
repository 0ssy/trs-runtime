ttack_001_duplicate_ids: BLOCKED | errors=['4.1 Immutability: record id already exists: dup']
attack_002_forged_authority: BLOCKED | errors=['6.1 Authorization Traceability: missing authorization records: ghost-capability']
attack_003_cycle_creation: BLOCKED | errors=['4.2 Causality: missing causes: self-cycle', '4.4 Closure: missing causes: self-cycle']
attack_004_schema_mismatch: BLOCKED | errors=['5.1 Schema Declaration: schema trs.observation.v1 does not match declared primitive Commitment']
attack_005_conflicting_commitments: BLOCKED | children=['c1', 'c2'], r2_errors=[]
attack_006_invalid_genesis: BLOCKED | errors=['5.2 Signature Presence: missing signature']
attack_007_transitive_capability: BLOCKED | d1_errors=['6.1 Authorization Traceability: missing authorization records: ghost-root'], d2_errors=['6.1 Authorization Traceability: missing authorization records: d1']
attack_008_payload_sniffing: BLOCKED | errors=['5.3 Payload Shape: missing payload keys: subject, value']
attack_009_query_mutation: BLOCKED | before=2, after=2
attack_010_hidden_conflict: BLOCKED | visible=['h1', 'h2']

Summary: 10/10 attacks blocked
←[31;1mtest_malformed_envelope_never_crashes_adapter (tests.test_fuzz_malformed_inputs.FuzzMalformedInputsTests.test_malformed_envelope_never_crashes_adapter) ... ok←[0m
←[31;1mtest_random_payload_for_declared_primitive_never_crashes_verifier (tests.test_fuzz_malformed_inputs.FuzzMalformedInputsTests.test_random_payload_for_declared_primitive_never_crashes_verifier) ... ok←[0m
←[31;1m←[0m
←[31;1m----------------------------------------------------------------------←[0m
←[31;1mRan 2 tests in 1.822s←[0m
←[31;1m←[0m
←[31;1mOK←[0m
Wrote byzantine campaign artifact: evidence\experiments\program6_byzantine_latest.json
Validation log: evidence\test_runs\2026-08-02T095328Z_validation_cycle.log
Failed steps:

- Benchmark gate

(venv) PS C:\Users\josep\OneDrive\Desktop\trs-runtime>
