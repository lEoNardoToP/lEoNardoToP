from __future__ import annotations

import asyncio
import os
import logging
import math
import platform
import socket

import httpx
import psutil

from .models import HostSnapshot, TelemetryBatch

logger = logging.getLogger(__name__)


def collect_host_snapshot() -> HostSnapshot:
    established = 0
    try:
        established = sum(
            1
            for conn in psutil.net_connections(kind="tcp")
            if conn.status == psutil.CONN_ESTABLISHED
        )
    except (psutil.AccessDenied, PermissionError):
        established = 0

    load_1m = 0.0
    if hasattr(os, "getloadavg"):
        load_1m = float(os.getloadavg()[0])

    return HostSnapshot(
        hostname=socket.gethostname(),
        cpu_percent=psutil.cpu_percent(interval=0.1),
        memory_percent=psutil.virtual_memory().percent,
        load_1m=max(load_1m, 0.0),
        process_count=len(psutil.pids()),
        established_tcp=established,
    )


async def run_agent(
    controller_url: str,
    interval_seconds: float = 5.0,
    agent_id: str | None = None,
) -> None:
    if (type(interval_seconds) not in (int, float)
            or not math.isfinite(interval_seconds) or not 0 < interval_seconds <= 3600):
        raise ValueError("interval_seconds must be finite and in (0, 3600]")
    endpoint = httpx.URL(controller_url)
    if endpoint.scheme not in ("http", "https") or not endpoint.host:
        raise ValueError("controller_url must be an absolute HTTP(S) URL")
    agent_id = agent_id or f"{platform.node()}-{os.getpid()}"
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                # psutil sampling blocks briefly; keep cancellation and other
                # coroutines responsive while the latest snapshot is collected.
                host = await asyncio.to_thread(collect_host_snapshot)
                batch = TelemetryBatch(agent_id=agent_id, host=host)
                response = await client.post(
                    f"{controller_url.rstrip('/')}/v1/telemetry",
                    json=batch.model_dump(mode="json"),
                )
                response.raise_for_status()
            except httpx.HTTPError as error:
                # Do not queue stale samples or spin during overload/outage.
                # Type-only diagnostics avoid exposing controller URLs or bodies.
                logger.warning("Telemetry delivery failed (%s)", type(error).__name__)
            except (OSError, psutil.Error) as error:
                logger.warning("Host collection failed (%s)", type(error).__name__)
            # Cancellation is intentionally not caught; the client context closes.
            await asyncio.sleep(interval_seconds)
