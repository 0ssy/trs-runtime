from __future__ import annotations

from dataclasses import dataclass

from .transport import InMemoryTransport, PendingDelivery


@dataclass
class PartitionController:
    transport: InMemoryTransport

    def disconnect(self, left: str, right: str) -> None:
        self.transport.partition(left, right)

    def reconnect(self, left: str, right: str) -> None:
        self.transport.heal(left, right)

    def reconnect_all(self) -> None:
        self.transport.heal_all()

    def flush(self) -> list[PendingDelivery]:
        return self.transport.flush()
