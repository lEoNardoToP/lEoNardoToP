"""Build and verify AtlasGuard on an isolated Docker network, without host ports."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
import asyncio
import json
import os
import time
import httpx
from atlasguard.agent import run_agent

base = "http://controller:8080"
with httpx.Client(timeout=5, trust_env=False) as client:
    for attempt in range(100):
        try:
            response = client.get(base + "/healthz")
            response.raise_for_status()
            assert response.json() == {"status": "ok"}
            break
        except httpx.HTTPError:
            time.sleep(0.1)
    else:
        raise RuntimeError("controller never became healthy")

async def exercise_agent():
    task = asyncio.create_task(run_agent(base, interval_seconds=0.1, agent_id="docker-proof"))
    try:
        async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
            for attempt in range(100):
                state = (await client.get(base + "/v1/state")).json()
                if state["batches"] >= 2:
                    return state["batches"]
                await asyncio.sleep(0.1)
        raise RuntimeError("Linux host agent did not deliver two snapshots")
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
agent_batches = asyncio.run(exercise_agent())

payload = {
    "agent_id": "docker-proof",
    "host": {"hostname": "qa", "cpu_percent": 1, "memory_percent": 2,
             "load_1m": 0, "process_count": 1, "established_tcp": 0},
    "inference": [],
}
def window(shift):
    return [{"service": "runtime-proof", "model": "v1", "latency_ms": 5,
             "status_code": 200, "feature_value": shift + i % 10} for i in range(100)]
with httpx.Client(timeout=5, trust_env=False) as client:
    for shift in (0, 0, 100):
        payload["inference"] = window(shift)
        result = client.post(base + "/v1/telemetry", json=payload)
        result.raise_for_status()
        outcome = result.json()
        if shift == 100:
            assert outcome["drifted"] and outcome["drift_score"] > 0.2, outcome
        elif outcome["drift_score"] is not None:
            assert outcome["drift_score"] == 0 and not outcome["drifted"], outcome
    payload["inference"] = []
    payload["runtime"] = [{"kind": "process", "uid": 0, "executable": "/bin/bash"}]
    response = client.post(base + "/v1/telemetry", json=payload)
    response.raise_for_status()
    assert {row["rule"] for row in response.json()["findings"]} == {"root-process", "interactive-shell"}
    metrics = client.get(base + "/metrics/")
    metrics.raise_for_status()
    assert 'atlasguard_drift_psi{model="v1",service="runtime-proof"}' in metrics.text
    before = client.get(base + "/v1/state").json()
    payload["host"]["cpu_percent"] = 101
    assert client.post(base + "/v1/telemetry", json=payload).status_code == 422
    assert client.get(base + "/v1/state").json() == before
assert os.getuid() != 0
print(json.dumps({"health": True, "linux_agent_batches": agent_batches,
                  "drift_shift_detected": True, "findings": True,
                  "prometheus": True, "invalid_batch_atomic": True, "non_root": True}))
'''


def command(argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    print(f"Running {argv[:2]}", flush=True)
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"{argv[:2]} failed: {result.stderr[-2000:]}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/docker-runtime.json")
    args = parser.parse_args()
    identity = uuid.uuid4().hex[:12]
    network, controller = f"atlasguard-qa-{identity}", f"atlasguard-controller-{identity}"
    probe, image = f"atlasguard-probe-{identity}", f"atlasguard:qa-{identity}"
    report = {"accepted": False, "cleanup_confirmed": False,
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted((ROOT / "src").rglob("*.py"))}}
    for relative in ("Dockerfile", "pyproject.toml", "scripts/verify_docker_runtime.py"):
        report["source_sha256"][relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    started = time.monotonic()
    created_network = False
    try:
        command(["docker", "build", "-t", image, "."], timeout=600)
        report["image_id"] = command(["docker", "image", "inspect", "--format", "{{.Id}}", image]).stdout.strip()
        command(["docker", "network", "create", "--internal", network])
        created_network = True
        policy = ["--network", network, "--read-only", "--cap-drop=ALL",
                  "--security-opt=no-new-privileges", "--memory=256m", "--pids-limit=64", "--cpus=1"]
        command(["docker", "run", "-d", "--name", controller, "--network-alias", "controller",
                 *policy, report["image_id"]])
        observation = command(["docker", "run", "--name", probe, *policy,
                               report["image_id"], "python", "-c", PROBE], timeout=90)
        report["checks"] = json.loads(observation.stdout)
        report["accepted"] = True
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
    finally:
        cleanup = []
        actions = [["docker", "rm", "-f", name] for name in (probe, controller)]
        if created_network:
            actions.append(["docker", "network", "rm", network])
        for argv in actions:
            try:
                result = subprocess.run(argv, capture_output=True, text=True,
                                        timeout=30, check=False)
                missing = argv[:3] == ["docker", "rm", "-f"] and result.stderr.strip() in {
                    f"Error response from daemon: No such container: {argv[-1]}",
                    f"Error: No such container: {argv[-1]}",
                }
                cleanup.append(result.returncode == 0 or missing)
            except (OSError, subprocess.TimeoutExpired):
                cleanup.append(False)
        report["cleanup_confirmed"] = all(cleanup)
        report["accepted"] = report["accepted"] and report["cleanup_confirmed"]
        report["elapsed_seconds"] = time.monotonic() - started
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
