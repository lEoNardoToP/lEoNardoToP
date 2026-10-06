from __future__ import annotations

from collections import defaultdict

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

from .drift import DriftDetector
from .models import IngestResult, TelemetryBatch
from .rules import RuntimeRuleEngine
from .store import EventStore

app = FastAPI(
    title="AtlasGuard",
    version="0.1.0",
    description="Linux-native ML observability, drift detection and runtime security.",
)

store = EventStore()
rules = RuntimeRuleEngine()
detectors: dict[str, DriftDetector] = defaultdict(DriftDetector)

INGESTED = Counter("atlasguard_batches_total", "Telemetry batches received")
FINDINGS = Counter(
    "atlasguard_findings_total",
    "Runtime findings emitted",
    labelnames=("severity", "rule"),
)
DRIFT_SCORE = Gauge(
    "atlasguard_drift_psi",
    "Latest Population Stability Index by service/model",
    labelnames=("service", "model"),
)
INFERENCE_LATENCY = Histogram(
    "atlasguard_inference_latency_ms",
    "Observed inference latency in milliseconds",
    labelnames=("service", "model"),
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)

app.mount("/metrics", make_asgi_app())


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/state")
def state() -> dict[str, object]:
    return store.snapshot()


@app.post("/v1/telemetry", response_model=IngestResult)
def ingest(batch: TelemetryBatch) -> IngestResult:
    INGESTED.inc()
    findings = []
    latest_score: float | None = None
    drifted = False

    for event in batch.runtime:
        event_findings = rules.evaluate(event)
        findings.extend(event_findings)
        for finding in event_findings:
            FINDINGS.labels(severity=finding.severity, rule=finding.rule).inc()

    for observation in batch.inference:
        INFERENCE_LATENCY.labels(
            service=observation.service, model=observation.model
        ).observe(observation.latency_ms)

        if observation.feature_value is None:
            continue

        key = f"{observation.service}:{observation.model}"
        score, is_drifted = detectors[key].observe(observation.feature_value)
        if score is not None:
            DRIFT_SCORE.labels(
                service=observation.service, model=observation.model
            ).set(score)
            latest_score = score
            drifted = drifted or is_drifted

    store.append(batch, findings)
    return IngestResult(
        findings=findings,
        drift_score=latest_score,
        drifted=drifted,
    )
