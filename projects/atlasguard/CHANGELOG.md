# Changelog

## 0.1.0 — 19 November 2026

First tagged release of the AtlasGuard control-plane prototype.

Included:
- Telemetry API (`POST /v1/telemetry`) with atomic batch admission and bounded series.
- PSI drift detection per service/model, explainable runtime rules, bounded event store.
- Prometheus metrics, Linux psutil agent, CLI (`serve`, `agent`, `demo`).
- Hardened Compose deployment: non-root, read-only root, dropped capabilities.

Fixed in this release:
- `GET /metrics` returned an empty 307 redirect to `/metrics/`, so the README's
  `curl http://127.0.0.1:8080/metrics` printed nothing. Both paths now return the
  exposition directly.

Verified (Linux, Python 3.13.18, 19 November 2026): 47 tests + 10 subtests, ruff clean,
and a live local run: `serve`, 120 baseline + 120 shifted demo samples (PSI 5.58),
a real agent posting host snapshots, findings and `/metrics` returning 200.
The Docker runtime probe (`scripts/verify_docker_runtime.py`) runs in CI; Docker Hub
was not reachable from the runner used for the local checks.

Known limits: in-memory store only, single controller, no authentication on the API.
