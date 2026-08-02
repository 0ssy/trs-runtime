from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.network_sync import sync_nodes
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import Verifier


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    outcome: str
    details: dict


def _seed_chain(store: RecordStore, count: int) -> list[Record]:
    records: list[Record] = [
        Record(
            id="g0",
            type=PrimitiveType.OBSERVATION,
            author="root",
            timestamp=datetime.now(timezone.utc),
            schema="trs.observation.v1",
            payload={"subject": "boot", "value": 1},
            signature="sig:g0",
        )
    ]
    for i in range(1, count):
        prev = records[-1].id
        records.append(
            Record(
                id=f"r{i}",
                type=PrimitiveType.INTENTION,
                author="alice",
                timestamp=datetime.now(timezone.utc),
                schema="trs.intention.v1",
                payload={"goal": f"g-{i}", "horizon": "Q1"},
                causes=(prev,),
                signature=f"sig:r{i}",
            )
        )
    for record in records:
        store.append(record)
    return records


def _scenario_replay_storm() -> ScenarioResult:
    source = RecordStore()
    target = RecordStore()
    _seed_chain(source, 60)
    verifier = Verifier(target)

    appended_total = 0
    for _ in range(20):
        result = sync_nodes(source, target, verifier)
        appended_total += len(result.appended_ids)
    survived = len(target.all()) == len(source.all())
    return ScenarioResult(
        name="replay_storm",
        outcome="TRS survives" if survived else "TRS broken",
        details={
            "source_records": len(source.all()),
            "target_records": len(target.all()),
            "appended_total": appended_total,
        },
    )


def _scenario_authorization_flood() -> ScenarioResult:
    store = RecordStore()
    verifier = Verifier(store)
    _seed_chain(store, 20)

    rejected = 0
    for i in range(100):
        forged = Record(
            id=f"f{i}",
            type=PrimitiveType.COMMITMENT,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.commitment.v1",
            payload={"action": "steal", "due_by": "2030-01-01"},
            causes=("r19",),
            authorization=(f"ghost-{i}",),
            signature=f"sig:f{i}",
        )
        result = verifier.verify(forged)
        if not result.valid:
            rejected += 1
    survived = rejected == 100
    return ScenarioResult(
        name="authorization_flood",
        outcome="TRS survives" if survived else "TRS broken",
        details={"attempts": 100, "rejected": rejected},
    )


def _scenario_cycle_spam() -> ScenarioResult:
    store = RecordStore()
    verifier = Verifier(store)
    _seed_chain(store, 10)

    rejected = 0
    for i in range(100):
        cyc = Record(
            id=f"c{i}",
            type=PrimitiveType.INTENTION,
            author="mallory",
            timestamp=datetime.now(timezone.utc),
            schema="trs.intention.v1",
            payload={"goal": "loop", "horizon": "Q2"},
            causes=(f"c{i}",),
            signature=f"sig:c{i}",
        )
        result = verifier.verify(cyc)
        if not result.valid:
            rejected += 1
    survived = rejected == 100
    return ScenarioResult(
        name="cycle_submission_spam",
        outcome="TRS survives" if survived else "TRS broken",
        details={"attempts": 100, "rejected": rejected},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Program 6: byzantine behavior campaign.")
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/program6_byzantine_latest.json",
        help="output JSON path",
    )
    args = parser.parse_args()

    scenarios = [_scenario_replay_storm(), _scenario_authorization_flood(), _scenario_cycle_spam()]
    any_broken = any(item.outcome == "TRS broken" for item in scenarios)
    overall = "TRS broken" if any_broken else "TRS survives"

    payload = {
        "program": "Program 6 - Byzantine",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_outcome": overall,
        "scenarios": [
            {"name": item.name, "outcome": item.outcome, "details": item.details}
            for item in scenarios
        ],
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote byzantine campaign artifact: {out_path}")
    return 1 if overall == "TRS broken" else 0


if __name__ == "__main__":
    raise SystemExit(main())
