# Drift input validation

The PSI implementation requires at least two histogram buckets and enough
finite observations in each distribution. `DriftDetector` uses ten buckets,
so its baseline and rolling window must each contain at least ten samples.
Invalid detector sizes and nonpositive/nonfinite thresholds now fail during
construction, rather than after telemetry has already been ingested.

Samples are converted consistently before bucket comparison. Nonfinite values
are rejected before state mutation, so a failed observation cannot contaminate
the baseline or rolling window. Tests verify both phases and recovery with a
valid unchanged distribution.

Local validation: 23 AtlasGuard tests passed on macOS/Python 3.11. The previous
source was separately executed and reproduced both NaN entering the baseline
and a size-one detector failing only after ingestion. This verifies numerical
input contracts; API lifecycle, cardinality bounds, deployment and concurrent
access still require further acceptance.

From the repository root with test dependencies installed:

```bash
PYTHONPATH=projects/atlasguard/src python -m pytest projects/atlasguard/tests -q
```

## HTTP admission and identity

The ASGI integration tests now cover health, ingestion, findings, state and
Prometheus output. Service/model identities use tuples, avoiding collisions
between `(a:b, c)` and `(a, b:c)`. Detector updates are serialized because
FastAPI synchronous endpoints execute in worker threads.

Every telemetry model rejects nonfinite floats before ingestion. A custom
validation-error response excludes rejected input values: otherwise FastAPI's
JSON response could fail while serializing the NaN/Infinity in a validation
error, changing a correct rejection into HTTP 500. Raw HTTP tests cover NaN,
positive/negative Infinity and exponent overflow, and verify no metrics,
baseline or event-store mutation occurs for an invalid batch.

Current local result: **33 tests passed**, including ten actual ASGI HTTP
cases. The numeric/rule and HTTP tests do not establish Linux-agent collection,
container deployment, authenticated ingestion or bounded metric cardinality;
those remain required follow-up. One dependency deprecation warning remains.

## Bounded cardinality and concurrent admission

The single-process controller admits at most **256 distinct service/model
pairs** over its lifetime. This includes latency-only observations, because
Prometheus labels allocate state even without a feature sample. A batch whose
new identities exceed the remaining budget receives HTTP **429** before any
metric, finding, drift baseline or event-store update. Existing identities
continue to ingest at capacity. Restart clears the in-memory identities and
baselines; there is no eviction that silently resets learned baselines.

One ingest lock covers reservation, detector updates and publication. The
concurrency regression submits eight distinct identities against a two-slot
budget: exactly two batches are admitted and six rejected, with two detectors
and two stored batches. Other regressions verify whole-batch rejection,
duplicate identities using one slot, and no latency-only quota bypass.

Parsed batches permit at most 256 inference observations and 256 runtime
events; identifiers and free-form event fields have explicit length bounds.
These are post-decoding schema bounds, **not a streaming HTTP body limit**.
A reverse-proxy/body-size limit and authenticated admission remain required
before deployment to an untrusted network. Multiple Uvicorn workers each own
independent capacity, counters and baselines: this remains a single-process
prototype, not shared distributed state.

Current local suite: **42 tests passed**, with one existing dependency warning.
