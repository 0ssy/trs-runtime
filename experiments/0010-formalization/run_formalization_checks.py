from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.record import PrimitiveType, Record
from runtime.storage import RecordStore
from runtime.verifier import Verifier


def _theorem_fail_safe_authorization() -> tuple[bool, str]:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    g0 = Record(
        id="g0",
        type=PrimitiveType.OBSERVATION,
        author="root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "boot", "value": 1},
        signature="sig:g0",
    )
    store.append(g0)
    forged = Record(
        id="x1",
        type=PrimitiveType.COMMITMENT,
        author="mallory",
        timestamp=datetime.now(timezone.utc),
        schema="trs.commitment.v1",
        payload={"action": "steal", "due_by": "2030-01-01"},
        authorization=("ghost-cap",),
        signature="sig:x1",
    )
    result = verifier.verify(forged)
    return (not result.valid, "unauthorized record rejected")


def _theorem_payload_independence() -> tuple[bool, str]:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    g0 = Record(
        id="g0",
        type=PrimitiveType.OBSERVATION,
        author="root",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "boot", "value": 1},
        signature="sig:g0",
    )
    store.append(g0)
    mismatch = Record(
        id="m1",
        type=PrimitiveType.COMMITMENT,
        author="alice",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "looks-like-observation", "value": 42},
        causes=("g0",),
        signature="sig:m1",
    )
    result = verifier.verify(mismatch)
    return (not result.valid, "declared primitive governs validation")


def _theorem_append_only_uniqueness() -> tuple[bool, str]:
    store = RecordStore()
    verifier = Verifier(store, allow_insecure_signatures=True, enforce_canonical_record_id=False)
    first = Record(
        id="dup",
        type=PrimitiveType.OBSERVATION,
        author="a",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "s", "value": 1},
        signature="sig:dup-1",
    )
    second = Record(
        id="dup",
        type=PrimitiveType.OBSERVATION,
        author="b",
        timestamp=datetime.now(timezone.utc),
        schema="trs.observation.v1",
        payload={"subject": "s", "value": 2},
        signature="sig:dup-2",
    )
    store.append(first)
    result = verifier.verify(second)
    return (not result.valid, "duplicate id rejected")


def main() -> int:
    parser = argparse.ArgumentParser(description="Program 8: theorem-style formalization checks.")
    parser.add_argument(
        "--out",
        type=str,
        default="evidence/experiments/program8_formalization_latest.json",
        help="output JSON path",
    )
    args = parser.parse_args()

    checks = {
        "T8.1 Fail-safe authorization": _theorem_fail_safe_authorization(),
        "T8.2 Payload independence": _theorem_payload_independence(),
        "T8.3 Append-only uniqueness": _theorem_append_only_uniqueness(),
    }
    failed = [name for name, (ok, _) in checks.items() if not ok]
    outcome = "TRS survives" if not failed else "TRS broken"
    payload = {
        "program": "Program 8 - Formalization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_outcome": outcome,
        "checks": {name: {"pass": ok, "note": note} for name, (ok, note) in checks.items()},
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote formalization artifact: {out_path}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
