from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terranode.terranode.identity_application import run_identity_vertical_slice


def main() -> None:
    result = run_identity_vertical_slice()
    print("Identity vertical slice result")
    print(f"accepted: {result.accepted_count}, rejected: {result.rejected_count}")
    print("directory:")
    for identity, controller in sorted(result.directory.items()):
        print(f"  - {identity} -> {controller}")
    print(f"proof count: {len(result.proofs)}")
    print("rejected reasons:")
    for receipt in result.submission_receipts:
        if not receipt.accepted:
            print(f"  - {receipt.identity or '<empty>'}: {receipt.reason}")


if __name__ == "__main__":
    main()
