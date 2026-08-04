from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terranode.terranode.application import run_vertical_slice


def main() -> None:
    result = run_vertical_slice()
    print("Vertical slice result")
    print(f"subject: {result.subject}")
    print(f"accepted: {result.accepted_count}, rejected: {result.rejected_count}")
    print(f"conflict claims: {result.conflict_claim_count}")
    print("allocations:")
    for claimant, granted in sorted(result.allocations.items()):
        print(f"  - {claimant}: {granted:.4f}")
    print(f"unresolved intentions: {len(result.unresolved_intentions)}")
    print(f"orphan commitments: {len(result.orphan_commitments)}")
    print(f"proof count: {len(result.proofs)}")


if __name__ == "__main__":
    main()
