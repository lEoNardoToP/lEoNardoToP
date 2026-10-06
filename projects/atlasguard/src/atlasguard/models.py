from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class HostSnapshot(BaseModel):
    hostname: str
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    load_1m: float = Field(ge=0)
    process_count: int = Field(ge=0)
    established_tcp: int = Field(ge=0)


class InferenceObservation(BaseModel):
    service: str
    model: str
    latency_ms: float = Field(ge=0)
    status_code: int = Field(ge=100, le=599)
    confidence: float | None = Field(default=None, ge=0, le=1)
    feature_value: float | None = None
    input_bytes: int = Field(default=0, ge=0)


class RuntimeEvent(BaseModel):
    kind: Literal["process", "network", "container"]
    executable: str | None = None
    uid: int | None = None
    destination_port: int | None = Field(default=None, ge=1, le=65535)
    privileged: bool = False
    image: str | None = None


class TelemetryBatch(BaseModel):
    agent_id: str
    observed_at: datetime = Field(default_factory=utc_now)
    host: HostSnapshot
    inference: list[InferenceObservation] = Field(default_factory=list)
    runtime: list[RuntimeEvent] = Field(default_factory=list)


class Finding(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    rule: str
    message: str


class IngestResult(BaseModel):
    accepted: bool = True
    findings: list[Finding]
    drift_score: float | None = None
    drifted: bool = False
