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
