from __future__ import annotations

from .policy import ProRataPolicy
from .runtime_adapter import TerraNodeRuntimeAdapter


def run_demo() -> dict[str, float]:
    adapter = TerraNodeRuntimeAdapter()
    policy = ProRataPolicy()

    alice = adapter.submit_intention(claimant="alice", subject="warehouse-7", amount=80.0, available=100.0)
    bob = adapter.submit_intention(claimant="bob", subject="warehouse-7", amount=60.0, available=100.0)
    if not alice.verification.valid or not bob.verification.valid:
        raise ValueError("intention submission failed")

    conflict_set = adapter.find_conflicts("warehouse-7")
    decision = policy.allocate(conflict_set)
    adapter.apply_allocations(decision)
    adapter.replay()

    return {allocation.claimant: allocation.granted for allocation in decision.allocations}


def main() -> None:
    results = run_demo()
    print("Final allocation")
    for claimant, granted in results.items():
        print(f"{claimant}: {granted:.2f} kg")


if __name__ == "__main__":
    main()
