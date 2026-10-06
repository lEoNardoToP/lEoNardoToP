from __future__ import annotations

import asyncio
import random
import socket
from pathlib import Path

import httpx
import typer
import uvicorn
from rich import print

from .agent import collect_host_snapshot, run_agent

app = typer.Typer(help="AtlasGuard CLI")


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8080,
) -> None:
    """Run the AtlasGuard control plane."""
    uvicorn.run("atlasguard.api:app", host=host, port=port, reload=False)


@app.command()
def agent(
    controller: str = "http://127.0.0.1:8080",
    interval: float = 5.0,
) -> None:
    """Run a Linux host telemetry agent."""
    asyncio.run(run_agent(controller, interval_seconds=interval))


@app.command()
def demo(
    controller: str = "http://127.0.0.1:8080",
    shifted: bool = False,
    count: int = 120,
) -> None:
    """Generate synthetic inference telemetry and one explainable runtime alert."""
    mean = 1.8 if shifted else 0.0

    with httpx.Client(timeout=10) as client:
        for index in range(count):
            payload = {
                "agent_id": f"demo-{socket.gethostname()}",
                "host": collect_host_snapshot().model_dump(),
                "inference": [
                    {
                        "service": "recommendation-api",
                        "model": "ranker-v3",
                        "latency_ms": random.uniform(20, 80),
                        "status_code": 200,
                        "confidence": random.uniform(0.65, 0.99),
                        "feature_value": random.gauss(mean, 1.0),
                        "input_bytes": random.randint(200, 4000),
                    }
                ],
                "runtime": [],
            }
            if index == count - 1:
                payload["runtime"] = [
                    {
                        "kind": "process",
                        "executable": "/bin/bash",
                        "uid": 0,
                        "privileged": True,
                    }
                ]
            response = client.post(f"{controller.rstrip('/')}/v1/telemetry", json=payload)
            response.raise_for_status()

    print(
        "[bold green]Demo sent.[/bold green] "
        "Use --shifted after a baseline run to trigger measurable drift."
    )


@app.command()
def architecture() -> None:
    """Print the path to the architecture documentation."""
    print(Path(__file__).resolve().parents[2] / "README.md")
