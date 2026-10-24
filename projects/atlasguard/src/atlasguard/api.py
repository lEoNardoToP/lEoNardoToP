from __future__ import annotations

from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


@app.exception_handler(RequestValidationError)
async def invalid_request(_request: Request, error: RequestValidationError) -> JSONResponse:
    # Pydantic errors can contain the rejected NaN/Infinity as input. Echoing
    # that value makes JSONResponse itself fail, turning admission into HTTP 500.
    details = [{"loc": item["loc"], "type": item["type"], "msg": item["msg"]}
               for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": details})


store = EventStore()
rules = RuntimeRuleEngine()
# Tuple identity avoids collisions such as ("a:b", "c") and ("a", "b:c").
detectors: dict[tuple[str, str], DriftDetector] = defaultdict(DriftDetector)
_detector_lock = Lock()

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

        key = (observation.service, observation.model)
        # FastAPI sync endpoints use worker threads. Baseline/window updates
        # form one state transition and must not interleave for the same key.
        with _detector_lock:
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
