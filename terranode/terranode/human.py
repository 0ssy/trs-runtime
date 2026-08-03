from __future__ import annotations

from dataclasses import dataclass

from .boundary import PublicSubmissionGateway, SubmissionOutcome, SubmissionRequest
from .runtime_adapter import TerraNodeRuntimeAdapter


@dataclass(frozen=True)
class QueuedSubmission:
    channel: str
    request: SubmissionRequest


class OfflineChannelClient:
    def __init__(self, *, channel: str) -> None:
        self.channel = channel
        self._queue: list[QueuedSubmission] = []

    def submit_offline(self, request: SubmissionRequest) -> None:
        self._queue.append(QueuedSubmission(channel=self.channel, request=request))

    def flush(self, *, gateway: PublicSubmissionGateway, adapter: TerraNodeRuntimeAdapter) -> list[SubmissionOutcome]:
        outcomes: list[SubmissionOutcome] = []
        for item in self._queue:
            outcomes.append(gateway.submit(adapter, item.request))
        self._queue.clear()
        return outcomes
