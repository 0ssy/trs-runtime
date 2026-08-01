# Attack Index

| ID | Title | Affected Rules | Status | Record | Script |
| --- | ----- | -------------- | ------ | ------ | ------ |
| ATTACK-001 | Duplicate ID | 4.1 Immutability | BLOCKED | `ATTACK-001_duplicate-id.md` | `attacks/attack_001_duplicate_ids.py` |
| ATTACK-002 | Forged Authority | 6.1 Authorization Traceability | BLOCKED | `ATTACK-002_forged-authority.md` | `attacks/attack_002_forged_authority.py` |
| ATTACK-003 | Cycle Creation | 4.2 Causality; 4.4 Closure | BLOCKED | `ATTACK-003_cycle-creation.md` | `attacks/attack_003_cycle_creation.py` |
| ATTACK-004 | Schema Mismatch | 5.1 Schema Declaration | BLOCKED | `ATTACK-004_schema-mismatch.md` | `attacks/attack_004_schema_mismatch.py` |
| ATTACK-005 | Conflicting Commitments Visibility | 4.5 Non-Silent Conflict | BLOCKED | `ATTACK-005_conflicting-commitments.md` | `attacks/attack_005_conflicting_commitments.py` |
| ATTACK-006 | Invalid Genesis | 5.2 Signature Presence | BLOCKED | `ATTACK-006_invalid-genesis.md` | `attacks/attack_006_invalid_genesis.py` |
| ATTACK-007 | Transitive Capability Forgery | 6.1 Authorization Traceability | BLOCKED | `ATTACK-007_transitive-capability.md` | `attacks/attack_007_transitive_capability.py` |
| ATTACK-008 | Payload Sniffing | 5.3 Payload Shape | BLOCKED | `ATTACK-008_payload-sniffing.md` | `attacks/attack_008_payload_sniffing.py` |
| ATTACK-009 | Query Mutation | 4.3 Local Sufficiency | BLOCKED | `ATTACK-009_query-mutation.md` | `attacks/attack_009_query_mutation.py` |
| ATTACK-010 | Hidden Conflict | 4.5 Non-Silent Conflict | BLOCKED | `ATTACK-010_hidden-conflict.md` | `attacks/attack_010_hidden_conflict.py` |
| ATTACK-011 | Malformed Envelope Fuzz | 5.3 Payload Shape; 6.1 Authorization Traceability | BLOCKED | `ATTACK-011_malformed-envelope-fuzz.md` | `tests/test_fuzz_malformed_inputs.py` |
| ATTACK-012 | Partition/Reconnection Sync | 4.2 Causality; 4.3 Local Sufficiency | BLOCKED | `ATTACK-012_partition-reconnection-sync.md` | `tests/test_multi_node_sim.py` |

Last verified run: `evidence/test_runs/2026-08-01_attack_suite.txt`
