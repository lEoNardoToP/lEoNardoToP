"""Minimal example: send one suspicious runtime event to AtlasGuard."""

import httpx

payload = {
    "agent_id": "example-node",
    "host": {
        "hostname": "ml-node-01",
        "cpu_percent": 37.4,
        "memory_percent": 58.2,
        "load_1m": 1.8,
        "process_count": 212,
        "established_tcp": 18,
    },
    "inference": [],
    "runtime": [
        {
            "kind": "network",
            "destination_port": 4444,
            "privileged": False,
        }
    ],
}

response = httpx.post("http://127.0.0.1:8080/v1/telemetry", json=payload, timeout=5)
response.raise_for_status()
print(response.json())
