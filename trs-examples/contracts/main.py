from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import client, commitment, observation


def main() -> None:
    c = client()
    subject = "contract:service-agreement"
    proposal = observation(
        author="buyer",
        subject=subject,
        value={"kind": "proposal", "terms": "deliver 10 units"},
    )
    c.submit(proposal)

    offer = commitment(
        author="seller",
        subject=subject,
        action="offer-service",
        due_by="2027-01-01",
        causes=[proposal["id"]],
        extra={"terms": "deliver 10 units"},
    )
    acceptance = commitment(
        author="buyer",
        subject=subject,
        action="accept-offer",
        due_by="2027-01-02",
        causes=[proposal["id"], offer["id"]],
        extra={"offer_id": offer["id"]},
    )
    c.submit(offer)
    c.submit(acceptance)

    replay = c.replay()
    print(
        {
            "subject": subject,
            "offer": offer["id"],
            "acceptance": acceptance["id"],
            "contracts_seen": len(replay.get("contracts", [])),
        }
    )


if __name__ == "__main__":
    main()
