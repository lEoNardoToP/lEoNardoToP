# AtlasGuard threat model

AtlasGuard is an observability and detection prototype, not an enforcement boundary.

## Assets

- inference telemetry and derived drift signals;
- Linux host/runtime telemetry;
- findings produced by deterministic runtime rules;
- availability of the control-plane API.

## Trust boundaries

1. **Agent -> control plane**: telemetry crosses a network boundary.
2. **Runtime source -> agent**: host/process information may be incomplete without elevated permissions.
3. **Control plane -> metrics backend**: exported labels must remain bounded to avoid cardinality abuse.

## Primary threats

| Threat | Current mitigation | Next hardening step |
|---|---|---|
| forged telemetry | strict Pydantic schema | mTLS + per-agent identity |
| replayed batches | timestamp captured | nonce/sequence validation |
| metrics cardinality abuse | fixed service/model labels in demo | allow-list + cardinality budget |
| compromised agent | least-privilege deployment guidance | signed agent builds + attestation |
| exposed control plane | non-root container, no added caps | authn/authz + network policy |
| blind spots in runtime events | explicit limitation | eBPF collector with bounded event schema |

## Design principle

Detection is explainable by default. Runtime findings include a stable rule identifier
and a human-readable reason. ML drift uses Population Stability Index rather than an
opaque model so an operator can reproduce the decision.

## Non-goals

- replacing an EDR;
- blocking processes or traffic;
- claiming kernel-level visibility without an eBPF collector;
- storing sensitive model inputs.
