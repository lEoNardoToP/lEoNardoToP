# AtlasGuard × Canonical

**Target:** Graduate Software Engineer — Open Source & Linux

## Why this project is relevant

AtlasGuard is a Linux-first engineering portfolio project built to make operational trade-offs visible in code rather than hidden behind a UI.

- A lightweight Linux agent collects host/process/network telemetry.
- A typed Python control plane validates and processes telemetry.
- The agent tolerates temporary controller/network failures instead of terminating.
- In-memory state is bounded.
- Docker deployment is non-root, read-only, and drops Linux capabilities.
- A systemd unit and explicit threat model are included.
- GitHub Actions validates lint, tests, and Docker build on Python 3.11 and 3.12.

## Engineering signals

| Canonical signal | AtlasGuard evidence |
|---|---|
| Linux knowledge | Linux host telemetry, systemd deployment, container hardening |
| High-quality resilient code | typed schemas, bounded state, failure-tolerant agent loop, tests |
| Security awareness | threat model, least-privilege runtime, explicit non-goals |
| Developer experience | CLI, quick-start, reproducible demo, readable docs |
| Beyond curriculum | public portfolio project built around production concerns |

## What I would extend next

1. Package the agent/control plane for Ubuntu and learn Debian packaging end-to-end.
2. Add structured journald integration and stronger service lifecycle behaviour.
3. Profile CPU/memory under sustained telemetry load and define explicit performance budgets.
4. Contribute reusable pieces upstream instead of keeping the project as a closed portfolio artifact.

## Honest scope

AtlasGuard is a portfolio prototype. It does **not** claim production-grade kernel visibility, distributed durability, or eBPF collection. Those are documented roadmap items rather than invented accomplishments.

**Author:** Leonardo Rosati — BSc Computer Science, University of Bologna (in progress)
