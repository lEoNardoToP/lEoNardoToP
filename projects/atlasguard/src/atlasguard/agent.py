from __future__ import annotations

import asyncio
import os
import platform
import socket

import httpx
import psutil

from .models import HostSnapshot, TelemetryBatch


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
    agent_id = agent_id or f"{platform.node()}-{os.getpid()}"
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            batch = TelemetryBatch(
                agent_id=agent_id,
                host=collect_host_snapshot(),
            )
            try:
                await client.post(
                    f"{controller_url.rstrip('/')}/v1/telemetry",
                    json=batch.model_dump(mode="json"),
                )
            except httpx.HTTPError:
                # Agent remains resilient to temporary controller/network failures.
                pass
            await asyncio.sleep(interval_seconds)
