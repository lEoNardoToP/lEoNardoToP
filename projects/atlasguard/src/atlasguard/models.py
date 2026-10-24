from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class TelemetryModel(BaseModel):
    # Reject before ingest mutates metrics or drift state; JSON cannot encode infinities.
    model_config = ConfigDict(allow_inf_nan=False)


class HostSnapshot(TelemetryModel):
    hostname: str = Field(min_length=1, max_length=253)
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    load_1m: float = Field(ge=0)
    process_count: int = Field(ge=0)
    established_tcp: int = Field(ge=0)


class InferenceObservation(TelemetryModel):
    service: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    latency_ms: float = Field(ge=0)
    status_code: int = Field(ge=100, le=599)
    confidence: float | None = Field(default=None, ge=0, le=1)
    feature_value: float | None = None
    input_bytes: int = Field(default=0, ge=0)


class RuntimeEvent(TelemetryModel):
    kind: Literal["process", "network", "container"]
    executable: str | None = Field(default=None, max_length=4096)
    uid: int | None = None
    destination_port: int | None = Field(default=None, ge=1, le=65535)
    privileged: bool = False
    image: str | None = Field(default=None, max_length=512)


class TelemetryBatch(TelemetryModel):
    agent_id: str = Field(min_length=1, max_length=128)
    observed_at: datetime = Field(default_factory=utc_now)
    host: HostSnapshot
    inference: list[InferenceObservation] = Field(default_factory=list, max_length=256)
    runtime: list[RuntimeEvent] = Field(default_factory=list, max_length=256)


class Finding(TelemetryModel):
    severity: Literal["low", "medium", "high", "critical"]
    rule: str
    message: str


class IngestResult(TelemetryModel):
    accepted: bool = True
    findings: list[Finding]
    drift_score: float | None = None
    drifted: bool = False
