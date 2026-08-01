from __future__ import annotations

from pathlib import Path
import importlib
import sys

ATTACKS = [
    "attack_001_duplicate_ids",
    "attack_002_forged_authority",
    "attack_003_cycle_creation",
    "attack_004_schema_mismatch",
    "attack_005_conflicting_commitments",
    "attack_006_invalid_genesis",
    "attack_007_transitive_capability",
    "attack_008_payload_sniffing",
    "attack_009_query_mutation",
    "attack_010_hidden_conflict",
]


def main() -> int:
    attacks_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(attacks_dir))

    blocked_count = 0
    for mod_name in ATTACKS:
        mod = importlib.import_module(mod_name)
        blocked, detail = mod.run()
        status = "BLOCKED" if blocked else "VULNERABLE"
        if blocked:
            blocked_count += 1
        print(f"{mod_name}: {status} | {detail}")

    total = len(ATTACKS)
    print(f"\nSummary: {blocked_count}/{total} attacks blocked")
    return 0 if blocked_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
