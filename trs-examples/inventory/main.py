from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import client, commitment, intention, observation


def main() -> None:
    c = client()
    subject = "inventory:warehouse-7"
    root = observation(author="inventory-root", subject=subject, value={"available": 100})
    c.submit(root)

    claim_a = intention(
        author="alice",
        subject=subject,
        goal="reserve-stock",
        horizon="today",
        causes=[root["id"]],
    )
    claim_b = intention(
        author="bob",
        subject=subject,
        goal="reserve-stock",
        horizon="today",
        causes=[root["id"]],
    )
    c.submit(claim_a)
    c.submit(claim_b)

    grant_a = commitment(
        author="allocator",
        subject=subject,
        action="grant-allocation",
        due_by="2027-01-01",
        causes=[root["id"], claim_a["id"]],
        extra={"claimant": "alice", "granted": 57.14},
    )
    grant_b = commitment(
        author="allocator",
        subject=subject,
        action="grant-allocation",
        due_by="2027-01-01",
        causes=[root["id"], claim_b["id"]],
        extra={"claimant": "bob", "granted": 42.86},
    )
    c.submit(grant_a)
    c.submit(grant_b)

    commitments = c.query({"type": "Commitment"})
    subject_commitments = [item["id"] for item in commitments if item.get("subject") == subject]
    print({"subject": subject, "commitments": len(subject_commitments)})


if __name__ == "__main__":
    main()
