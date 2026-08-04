from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terranode.terranode.reputation_application import run_reputation_vertical_slice


def main() -> None:
    result = run_reputation_vertical_slice()
    print("Reputation vertical slice result")
    print(f"accepted: {result.accepted_count}, rejected: {result.rejected_count}")
    print("weights:")
    for claimant, weight in sorted(result.weights.items()):
        print(f"  - {claimant}: {weight:.6f}")
    print("allocations:")
    for claimant, granted in sorted(result.allocations.items()):
        print(f"  - {claimant}: {granted:.4f}")
    print(f"proof count: {len(result.proofs)}")


if __name__ == "__main__":
    main()
