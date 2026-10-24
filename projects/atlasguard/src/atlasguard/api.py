from __future__ import annotations

from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
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
MAX_SERIES = 256
_admitted_series: set[tuple[str, str]] = set()
_ingest_lock = Lock()

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
    # Reserve all identities before metrics or state mutation. A latency-only
    # observation creates Prometheus labels too, even without a drift sample.
    identities = {(item.service, item.model) for item in batch.inference}
    with _ingest_lock:
        if len(_admitted_series | identities) > MAX_SERIES:
            raise HTTPException(status_code=429, detail="Service/model capacity reached")
        _admitted_series.update(identities)
        return _ingest_admitted(batch)


def _ingest_admitted(batch: TelemetryBatch) -> IngestResult:
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
        # The caller holds the ingest lock through baseline, metrics and store
        # publication; concurrent batches cannot reserve the same final slot.
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
