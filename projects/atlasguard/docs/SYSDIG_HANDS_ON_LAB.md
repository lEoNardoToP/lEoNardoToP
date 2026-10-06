# AtlasGuard × Sysdig — Hands-on Lab

**Target:** Junior AI & Product Enablement Specialist — Italy / Remote

## Learning goal

Use a small, reproducible lab to explain how runtime telemetry becomes an explainable security finding, while being explicit about the visibility boundary of the prototype.

## Prerequisites

- Python 3.11+
- Docker (optional for the containerized path)
- basic Linux and HTTP familiarity

## 15-minute lab

### 1. Start

Run the AtlasGuard control plane and open the API and Prometheus metrics endpoints.

### 2. Observe normal telemetry

Send ordinary host and inference telemetry. Confirm that the service is healthy and no runtime findings are emitted.

### 3. Trigger a suspicious runtime scenario

Inject events such as:

- privileged workload;
- process running as uid 0;
- `/bin/bash` execution;
- outbound connection to port `4444`;
- mutable container image tag `:latest`.

### 4. Explain the findings

Each finding has a stable rule identifier and a human-readable reason. The learner can map the output directly back to the event fields that caused it and discuss likely false positives.

### 5. Extend the lab

Replace the synthetic runtime event source with a Falco/eBPF-backed event source while preserving the control-plane contract.

## Why this maps to technical enablement

- **Hands-on lab construction:** repeatable Python/Docker scenarios rather than slides only.
- **Technical writing:** architecture README, threat model, quick start, and explicit non-goals.
- **Automation:** CI validates Python versions, tests, linting, and Docker build.
- **Cloud-native curiosity:** Linux runtime events, containers, least-privilege deployment, and a direct path toward Falco/eBPF collection.

## Honest scope

AtlasGuard is **not** presented as a replacement for Sysdig or Falco. The runtime events in the current prototype are user-space inputs. The value of the lab is that it makes the underlying concepts inspectable and teachable and leaves a technically honest path toward real kernel event collection.

**Author:** Leonardo Rosati — BSc Computer Science, University of Bologna (in progress)
