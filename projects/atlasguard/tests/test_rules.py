from atlasguard.models import RuntimeEvent
from atlasguard.rules import RuntimeRuleEngine


def test_shell_as_root_is_explainably_flagged() -> None:
    findings = RuntimeRuleEngine().evaluate(
        RuntimeEvent(
            kind="process",
            executable="/bin/bash",
            uid=0,
            privileged=True,
        )
    )

    rules = {finding.rule for finding in findings}
    assert "interactive-shell" in rules
    assert "root-process" in rules
    assert "privileged-runtime" in rules


def test_uncommon_egress_port_is_flagged() -> None:
    findings = RuntimeRuleEngine().evaluate(
        RuntimeEvent(kind="network", destination_port=4444)
    )
    assert any(finding.rule == "uncommon-egress-port" for finding in findings)


def test_normal_network_event_is_clean() -> None:
    findings = RuntimeRuleEngine().evaluate(
        RuntimeEvent(kind="network", destination_port=443)
    )
    assert findings == []
