"""Exercise telemetry admission and drift identity through actual ASGI requests."""
from collections import defaultdict

import pytest
from fastapi.testclient import TestClient

from atlasguard import api
from atlasguard.drift import DriftDetector
from atlasguard.store import EventStore


def batch(observations=None):
    return {
        "agent_id": "review-agent",
        "host": {"hostname": "test", "cpu_percent": 1, "memory_percent": 2,
                 "load_1m": 0, "process_count": 1, "established_tcp": 0},
        "inference": observations or [],
    }


def observation(service="service", model="model", value=1.0):
    return {"service": service, "model": model, "latency_ms": 3,
            "status_code": 200, "feature_value": value}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "store", EventStore())
    monkeypatch.setattr(api, "detectors", defaultdict(
        lambda: DriftDetector(baseline_size=10, window_size=10)))
    with TestClient(api.app) as session:
        yield session


def test_health_telemetry_findings_state_and_metrics(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    payload = batch([observation()])
    payload["runtime"] = [{"kind": "process", "executable": "/bin/bash", "uid": 0}]
    response = client.post("/v1/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"]
    assert {row["rule"] for row in response.json()["findings"]} == {"interactive-shell", "root-process"}
    assert client.get("/v1/state").json()["batches"] == 1
    assert "atlasguard_inference_latency_ms_count" in client.get("/metrics/").text


def test_delimiter_collisions_do_not_share_a_drift_baseline(client):
    # These two identities were concatenated to the same 'a:b:c' key.
    for _ in range(10):
        assert client.post("/v1/telemetry", json=batch([
            observation("a:b", "c", 0), observation("a", "b:c", 100)
        ])).status_code == 200
    assert len(api.detectors) == 2
    for _ in range(10):
        response = client.post("/v1/telemetry", json=batch([
            observation("a:b", "c", 0), observation("a", "b:c", 100)
        ]))
    assert response.json()["drift_score"] == 0
    assert not response.json()["drifted"]


@pytest.mark.parametrize("field", ["feature_value", "latency_ms"])
@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e309"])
def test_nonfinite_telemetry_rejected_before_any_mutation(client, field, token):
    import json
    item = observation()
    item[field] = "REPLACE_NONFINITE"
    # Raw JSON also exercises the HTTP decoder's permissive NaN handling.
    raw = json.dumps(batch([observation(), item])).replace('"REPLACE_NONFINITE"', token)
    count = api.INGESTED._value.get()
    response = client.post("/v1/telemetry", content=raw, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert api.INGESTED._value.get() == count
    assert client.get("/v1/state").json()["batches"] == 0
    assert len(api.detectors) == 0
