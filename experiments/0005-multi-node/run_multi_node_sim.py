from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.multi_node_sim import fully_connected_links, make_linear_records, make_node, simulate_partitioned_sync


def main() -> int:
    chain = make_linear_records(20)
    nodes = [
        make_node("n0", chain),
        make_node("n1", chain[:10]),
        make_node("n2", chain[:5]),
        make_node("n3", []),
        make_node("n4", []),
        make_node("n5", []),
    ]
    rounds = [
        [("n0", "n1"), ("n2", "n3"), ("n4", "n5")],
        [("n0", "n1"), ("n2", "n3"), ("n4", "n5")],
        [("n1", "n2"), ("n3", "n4")],
        fully_connected_links([node.name for node in nodes]),
        fully_connected_links([node.name for node in nodes]),
    ]
    result = simulate_partitioned_sync(nodes, rounds)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "converged": result.converged,
        "rounds": [
            {
                "round": item.round_index,
                "links": item.links,
                "rejected_by_target": item.rejected_by_target,
            }
            for item in result.rounds
        ],
        "inventories": result.inventories,
    }
    print(json.dumps(payload, indent=2))
    out = Path("evidence") / "traces" / "2026-08-01_multi_node_sim.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if result.converged else 1


if __name__ == "__main__":
    raise SystemExit(main())
