from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Program 10: generate independent attack handoff packet.")
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/program10_independent_attack_packet.json",
        help="output JSON path",
    )
    args = parser.parse_args()

    packet = {
        "program": "Program 10 - Independent Attack",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "objective": "Have an external evaluator attempt to break TRS runtime behavior.",
        "rules": [
            "Do not improve design; attempt to break it.",
            "Report concrete exploit attempt steps and evidence artifacts.",
            "Classify each attempt as blocked, partial, or successful breach.",
        ],
        "starter_commands": [
            "python attacks/run_attacks.py",
            "python -m unittest -v tests.test_fuzz_malformed_inputs",
            "python experiments/0008-byzantine/run_byzantine_campaign.py",
            "python experiments/0006-validation/run_validation_cycle.py --gate-mode nightly",
        ],
        "expected_outputs": [
            "attack transcripts",
            "proof-of-break (if any)",
            "reproduction commands",
            "proposed TRS-0002 trigger rationale (if applicable)",
        ],
        "default_cycle_outcome": "NEED_MORE_EVIDENCE",
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(f"Wrote independent-attack packet: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
