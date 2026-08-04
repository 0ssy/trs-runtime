from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import client, commitment, observation


def main() -> None:
    c = client()
    subject = "identity-registry:demo"
    registry = observation(author="identity-root", subject=subject, value={"registry": "demo-v1"})
    c.submit(registry)

    alice_registration = observation(
        author="alice",
        subject=subject,
        value={"identity": "did:trs:alice", "controller": "alice"},
        causes=[registry["id"]],
    )
    c.submit(alice_registration)

    attestation = commitment(
        author="registrar",
        subject=subject,
        action="attest-identity",
        due_by="2027-01-01",
        causes=[registry["id"], alice_registration["id"]],
        extra={"identity": "did:trs:alice"},
    )
    c.submit(attestation)

    alice_records = c.query({"author": "alice"})
    print({"identity": "did:trs:alice", "records_by_alice": len(alice_records), "attestation": attestation["id"]})


if __name__ == "__main__":
    main()
