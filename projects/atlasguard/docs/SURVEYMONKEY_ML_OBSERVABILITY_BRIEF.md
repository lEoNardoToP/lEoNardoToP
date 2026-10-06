# AtlasGuard × SurveyMonkey

**Target:** Machine Learning Engineer — Italy / Remote

## Why this project is relevant

AtlasGuard treats model reliability as a platform concern rather than logic embedded inside one model implementation.

- Inference observations carry service/model identity, latency, confidence, input size, and an optional numeric feature signal.
- Population Stability Index compares a reference distribution with a rolling production window.
- Drift is exported as a Prometheus gauge alongside latency and system metrics.
- The control plane avoids storing raw prompts, survey answers, or model inputs.
- The detector is isolated from ingestion so it can be replaced by KS tests, embedding-distance monitoring, or task-specific evaluation without changing the telemetry contract.

## Engineering signals

| ML platform signal | AtlasGuard evidence |
|---|---|
| Production monitoring | Prometheus counters, histograms, gauges |
| Model deterioration signal | PSI baseline + rolling window |
| Platform separation | telemetry contract is model-agnostic |
| CI/CD mindset | automated lint/test matrix + Docker build |
| Privacy-aware design | metadata/features instead of raw user content |

## Demonstrated failure mode

A reference distribution and a shifted current distribution produced **PSI = 7.83** against a configured **0.20** threshold while the API itself remained healthy. This is the core point of the demo: model reliability can deteriorate while ordinary service-health checks still look fine.

## What I would extend next

1. Per-feature and model-version baseline registry.
2. Online evaluation hooks and richer feedback loops.
3. Durable event storage, retention policies, cardinality budgets, and back-pressure metrics.
4. OpenTelemetry ingestion/export and Kubernetes deployment primitives.
5. Streaming integration and explicit load/SLO testing.

## Honest scope

The current project demonstrates monitoring mechanics; it does **not** claim AWS, Kafka, EKS, or SageMaker production experience. Those technologies are a learning and extension path, not resume inflation.

**Author:** Leonardo Rosati — BSc Computer Science, University of Bologna (in progress)
