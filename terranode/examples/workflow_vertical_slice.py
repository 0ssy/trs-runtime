from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terranode.terranode.workflow_application import run_workflow_vertical_slice


def main() -> None:
    result = run_workflow_vertical_slice()
    print("Workflow vertical slice result")
    print(f"accepted: {result.accepted_count}, rejected: {result.rejected_count}")
    print(f"converged: {result.converged}")
    print("allocations:")
    for claimant, granted in sorted(result.allocations.items()):
        print(f"  - {claimant}: {granted:.4f}")
    print(f"proof count: {len(result.proofs)}")


if __name__ == "__main__":
    main()
