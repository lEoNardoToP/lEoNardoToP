# Agent delivery and failure behavior

The agent samples one latest host snapshot per iteration, submits it to the
controller and sleeps for the configured interval after success or failure.
There is no unbounded retry queue of stale telemetry.

HTTP error responses now call `raise_for_status`: a 429/500 is a rejected
sample, not a successful delivery. Network errors and collection OS errors
produce type-only warnings, excluding controller URLs, response bodies and
filesystem diagnostics. The next scheduled iteration may recover. Cancellation
is propagated and the HTTP client context closes.

Intervals must be finite and in `(0, 3600]`; invalid values fail before client
creation or sampling. The controller must be an absolute HTTP(S) URL. Snapshot
collection runs in a worker thread so psutil's synchronous sampling does not
block the event loop. Cancelling the coroutine cannot preempt an already
executing psutil call; it can finish in that bounded-work thread.

## Verified contracts

The complete local suite passed **46 tests and 10 subtests**. New tests use a
real HTTPX client with an in-memory transport to exercise connection failure,
429, 500 and subsequent recovery; paced collection failure; cancellation during
HTTP delivery; and a different thread for snapshot collection. They verify
client closure and rejection of invalid options before I/O. These are real
client lifecycle checks with simulated transport, not Linux/network deployment
acceptance. The host collector, systemd and container operation still need
runtime checks in their target environments.

From the repository root with the declared dependencies installed:

```bash
PYTHONPATH=projects/atlasguard/src python -m pytest projects/atlasguard/tests -q
```

The HTTP deadline remains ten seconds per client request. Sampling time plus
request time plus the post-attempt interval determine the actual cadence;
`--interval` is not a fixed-rate scheduling guarantee. Logs can contain one
warning per failed iteration; deployment should choose a suitable interval
and log retention policy.
