from __future__ import annotations

from dataclasses import dataclass

from .models import Finding, RuntimeEvent


@dataclass(frozen=True)
class RuntimeRuleEngine:
    """Deterministic rule engine for explainable runtime findings."""

    suspicious_shells: tuple[str, ...] = (
        "/bin/sh",
        "/bin/bash",
        "/usr/bin/zsh",
        "/usr/bin/nc",
        "/usr/bin/ncat",
    )
    uncommon_outbound_ports: tuple[int, ...] = (4444, 5555, 6667, 9001)

    def evaluate(self, event: RuntimeEvent) -> list[Finding]:
        findings: list[Finding] = []

        if event.privileged:
            findings.append(
                Finding(
                    severity="high",
                    rule="privileged-runtime",
                    message="Privileged container/runtime activity observed.",
                )
            )

        if event.uid == 0 and event.kind == "process":
            findings.append(
                Finding(
                    severity="medium",
                    rule="root-process",
                    message="Process executed as uid=0; verify this is expected.",
                )
            )

        if event.executable and event.executable in self.suspicious_shells:
            findings.append(
                Finding(
                    severity="high",
                    rule="interactive-shell",
                    message=f"Shell-like executable observed: {event.executable}",
                )
            )

        if event.kind == "network" and event.destination_port in self.uncommon_outbound_ports:
            findings.append(
                Finding(
                    severity="high",
                    rule="uncommon-egress-port",
                    message=f"Outbound connection to unusual port {event.destination_port}.",
                )
            )

        if event.image and event.image.endswith(":latest"):
            findings.append(
                Finding(
                    severity="low",
                    rule="mutable-image-tag",
                    message="Container uses mutable :latest tag; pin an immutable digest.",
                )
            )

        return findings
