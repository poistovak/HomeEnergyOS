from dataclasses import replace

import pytest

from heos.execution_supervisor import (
    ApprovalToken,
    ContinuityDirective,
    ExecutionPolicy,
    ExecutionStatus,
    ExecutionSupervisor,
)


def directive(**changes):
    values = {
        "plan_id": "plan-001",
        "incident_id": "incident-001",
        "status": "automatic",
        "action": "apply_fallback",
        "max_attempts": 3,
        "cooldown_seconds": 10,
        "deadline": 500,
        "approval_token_required": False,
        "source_digest": "abc123",
        "metadata": {"source": "m25"},
    }
    values.update(changes)
    return ContinuityDirective(**values)


def approval(**changes):
    values = {"token_id": "approval-1", "plan_id": "plan-001", "approved_action": "apply_fallback", "valid_until": 400, "issuer": "operator"}
    values.update(changes)
    return ApprovalToken(**values)


def test_automatic_directive_is_ready():
    cert = ExecutionSupervisor().supervise(directive(), now=100)
    assert cert.command.status is ExecutionStatus.READY
    assert cert.command.attempt_limit == 3
    assert cert.verify()


def test_approval_required_waits_without_token():
    cert = ExecutionSupervisor().supervise(directive(status="approval_required", approval_token_required=True), now=100)
    assert cert.command.status is ExecutionStatus.WAITING_APPROVAL
    assert cert.command.attempt_limit == 0


def test_valid_approval_unlocks_execution():
    cert = ExecutionSupervisor().supervise(directive(approval_token_required=True), now=100, approval=approval())
    assert cert.command.status is ExecutionStatus.READY


@pytest.mark.parametrize("token", [approval(valid_until=99), approval(plan_id="other"), approval(approved_action="other")])
def test_invalid_approval_is_rejected(token):
    cert = ExecutionSupervisor().supervise(directive(approval_token_required=True), now=100, approval=token)
    assert cert.command.status is ExecutionStatus.WAITING_APPROVAL


def test_blocked_directive_is_rejected():
    cert = ExecutionSupervisor().supervise(directive(status="blocked", max_attempts=0), now=100)
    assert cert.command.status is ExecutionStatus.REJECTED
    assert cert.command.action == "no_op"


def test_expired_directive():
    cert = ExecutionSupervisor().supervise(directive(deadline=99), now=100)
    assert cert.command.status is ExecutionStatus.EXPIRED


def test_policy_caps_attempts():
    supervisor = ExecutionSupervisor(policy=ExecutionPolicy(maximum_attempts=2))
    assert supervisor.supervise(directive(max_attempts=5), now=100).command.attempt_limit == 2


def test_zero_attempts_are_rejected():
    cert = ExecutionSupervisor().supervise(directive(max_attempts=0), now=100)
    assert cert.command.status is ExecutionStatus.REJECTED


def test_deterministic_command():
    first = ExecutionSupervisor().supervise(directive(), now=100)
    second = ExecutionSupervisor().supervise(directive(), now=100)
    assert first.command.command_id == second.command.command_id
    assert first.digest == second.digest


def test_ledger_chain_and_tamper_detection():
    supervisor = ExecutionSupervisor()
    first = supervisor.supervise(directive(), now=100)
    second = supervisor.supervise(directive(plan_id="plan-002"), now=101)
    assert second.previous_digest == first.digest
    assert supervisor.ledger.verify_chain()
    assert not replace(first, digest="0" * 64).verify()


def test_validation():
    with pytest.raises(ValueError):
        directive(plan_id="")
    with pytest.raises(ValueError):
        ExecutionPolicy(maximum_attempts=0)
    with pytest.raises(ValueError):
        ExecutionSupervisor().supervise(directive(), now=-1)


def test_json_export():
    exported = ExecutionSupervisor().supervise(directive(), now=100).to_json()
    assert '"policy_version":"26.0.0"' in exported
    assert '"status":"ready"' in exported
