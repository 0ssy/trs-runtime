from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terranode.terranode.policy import ProRataPolicy
from terranode.terranode.runtime_adapter import TerraNodeRuntimeAdapter


def main() -> None:
    node_a = TerraNodeRuntimeAdapter(node_id="node-a")
    node_b = TerraNodeRuntimeAdapter(node_id="node-b")

    node_a.seed_subject(
        subject="warehouse-north",
        available=100.0,
        root_id="warehouse-north-root",
        capability_id="warehouse-north-capability",
    )
    node_b.seed_subject(
        subject="warehouse-north",
        available=100.0,
        root_id="warehouse-north-root",
        capability_id="warehouse-north-capability",
    )

    node_a.submit_intention("alice", "warehouse-north", 80.0, 100.0)
    node_b.submit_intention("bob", "warehouse-north", 60.0, 100.0)

    before_a = node_a.find_conflicts("warehouse-north")
    before_b = node_b.find_conflicts("warehouse-north")
    print(f"Before reconnect: node-a claims={len(before_a.claims)} node-b claims={len(before_b.claims)}")

    node_a.sync_with_peer(node_b)
    after = node_a.find_conflicts("warehouse-north")
    decision = ProRataPolicy().allocate(after)
    node_a.apply_allocations(decision)
    node_a.sync_with_peer(node_b)

    print(f"After reconnect: shared claims={len(after.claims)}")
    for allocation in decision.allocations:
        print(f"{allocation.claimant}: {allocation.granted:.2f} kg")
    print(f"Converged inventories: {sorted(r.id for r in node_a.store.all()) == sorted(r.id for r in node_b.store.all())}")


if __name__ == "__main__":
    main()
