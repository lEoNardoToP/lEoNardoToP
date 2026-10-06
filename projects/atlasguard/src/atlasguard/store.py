from __future__ import annotations

from collections import deque
from threading import Lock

from .models import Finding, TelemetryBatch


class EventStore:
    def __init__(self, max_batches: int = 1000) -> None:
        self._batches: deque[TelemetryBatch] = deque(maxlen=max_batches)
        self._findings: deque[Finding] = deque(maxlen=max_batches * 4)
        self._lock = Lock()

    def append(self, batch: TelemetryBatch, findings: list[Finding]) -> None:
        with self._lock:
            self._batches.append(batch)
            self._findings.extend(findings)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "batches": len(self._batches),
                "findings": len(self._findings),
                "recent_findings": [item.model_dump() for item in list(self._findings)[-20:]],
            }
