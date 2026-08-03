from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.multi_node_sim import fully_connected_links, make_linear_records, make_node, simulate_partitioned_sync
from runtime.record import PrimitiveType, Record


EVIDENCE_DIR = ROOT / "evidence" / "redteam"
LATEST_PATH = EVIDENCE_DIR / "cycle0016_latest.json"


def _run_attacks() -> dict[str, object]:
    proc = subprocess.run([sys.executable, "attacks/run_attacks.py"], cwd=ROOT, capture_output=True, text=True)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    summary_line = next((line for line in reversed(lines) if line.startswith("Summary:")), "")
    return {
        "command": f"{sys.executable} attacks/run_attacks.py",
        "exit_code": proc.returncode,
        "summary": summary_line,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _inject_malicious_record(attacker_node) -> str:
    malicious = Record(
        id="malicious-forged-0001",
        type=PrimitiveType.COMMITMENT,
        author="mallory",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"action": "steal", "due_by": "2027-01-01"},
        causes=("g0",),
        authorization=("ghost-cap",),
        signature="sig:malicious-forged-0001",
        subject="warehouse-7",
    )
    attacker_node.store.append(malicious)
    return malicious.id


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

    seed = make_linear_records(250)
    node_a = make_node("node-a", seed=seed)
    node_b = make_node("node-b", seed=seed)
    node_c = make_node("node-c", seed=seed)
    node_d = make_node("node-d", seed=seed)
    nodes = [node_a, node_b, node_c, node_d]

    malicious_id = _inject_malicious_record(node_d)
    rounds = [fully_connected_links([node.name for node in nodes]) for _ in range(2)]
    sim = simulate_partitioned_sync(nodes, rounds)

    rejected_targets: dict[str, list[str]] = {}
    for round_result in sim.rounds:
        for target, rejected in round_result.rejected_by_target.items():
            rejected_targets.setdefault(target, [])
            rejected_targets[target].extend(rejected)

    honest_nodes = [node_a, node_b, node_c]
    malicious_on_honest = {
        node.name: node.store.exists(malicious_id)
        for node in honest_nodes
    }
    honest_inventories_equal = len(
        {tuple(sorted(record.id for record in node.store.all())) for node in honest_nodes}
    ) == 1

    attacks = _run_attacks()
    baseline_pass = (
        attacks["exit_code"] == 0
        and not any(malicious_on_honest.values())
        and honest_inventories_equal
    )

    summary = {
        "timestamp": timestamp,
        "status": "in_progress",
        "seed_records": len(seed),
        "malicious_record_id": malicious_id,
        "rejected_by_target": rejected_targets,
        "malicious_present_on_honest_nodes": malicious_on_honest,
        "honest_inventories_equal": honest_inventories_equal,
        "multi_node_converged_flag": sim.converged,
        "attack_suite": attacks,
        "baseline_pass": baseline_pass,
        "closure_note": "External live red-team campaign remains required for cycle closure.",
    }

    summary_path = EVIDENCE_DIR / f"{timestamp}_cycle0016_redteam_sim.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary: {summary_path.relative_to(ROOT)}")
    print(f"Baseline pass: {baseline_pass}")
    return 0 if baseline_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
