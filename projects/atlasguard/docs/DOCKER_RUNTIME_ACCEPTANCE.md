# Real controller and Linux-agent runtime acceptance

The repeatable probe builds the application image and runs two non-root
containers on a disposable internal Docker network, with no published host
ports. Both use read-only roots, dropped capabilities, no-new-privileges and
CPU/memory/PID limits. This exercises the actual installed package and Linux
psutil collector, not a mocked transport.

Verified behavior:

- health endpoint becomes ready;
- the real async Linux host agent delivers at least two snapshots over HTTP
  and cancels cleanly;
- a 100-sample baseline and matching window yield no drift;
- a shifted 100-sample window triggers the expected drift score;
- process events produce the documented findings;
- Prometheus exposes the service/model drift series;
- an invalid batch receives 422 without changing stored state;
- probe runs non-root, and container/network cleanup is confirmed.

Run from `projects/atlasguard` with Python 3 and a working Docker daemon:

```bash
python scripts/verify_docker_runtime.py
```

The JSON report under ignored `reports/` records image identity, source/build/
probe hashes, individual checks and cleanup. A failed build, probe or cleanup
returns nonzero. The workflow now requires this runtime proof after lint and
unit/HTTP tests, and uploads its JSON on both success and failure.

[Executed final local report](evidence/docker-runtime.json) passed in about
8.7 seconds with an already-cached image build; that is a local observation,
not a deployment startup SLO. The earlier cold-build run also passed. The
Python suite remains 46 passed plus 10 subtests, and Ruff passed.

This is a single-process deployment check, not authentication, streaming body
limits, shared multi-worker state, persistence, Prometheus-server integration,
systemd service installation or multi-host reliability acceptance. The
Prometheus endpoint is exercised; a separate Prometheus server is not launched.
The base tag and Python dependency ranges remain mutable; the report identifies
the image actually tested rather than claiming a reproducible pinned environment.
