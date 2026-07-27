from __future__ import annotations

from dataclasses import replace

import pytest

from heos.continuity import (
    ContinuityExecutionBridge,
    ContinuityGovernor,
    ContinuityStatus,
    RecoveryMode,
    RecoverySnapshot,
)
from heos.execution_supervisor import (
    ApprovalToken,
    ExecutionStatus,
    ExecutionSupervisor,
)


def recovery(
    *,
    mode: RecoveryMode = RecoveryMode.FALLBACK,
    severity: int = 30,
    fallback_strategy: str | None = "last_known_safe_plan",
) -> RecoverySnapshot:
    return RecoverySnapshot(
        incident_id="incident-136",
        mode=mode,
        severity=severity,
        fallback_strategy=fallback_strategy,
        valid_until=1000,
        metadata={"source": "test-136"},
    )


def certificate(
    *,
    mode: RecoveryMode = RecoveryMode.FALLBACK,
    severity: int = 30,
    fallback_strategy: str | None = "last_known_safe_plan",
):
    return ContinuityGovernor().govern(
        recovery(
            mode=mode,
            severity=severity,
            fallback_strategy=fallback_strategy,
        ),
        now=100,
    )


def test_automatic_plan_becomes_ready_execution():
    certified = certificate()

    directive = ContinuityExecutionBridge().build(certified)

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
    )

    assert certified.plan.status is ContinuityStatus.AUTOMATIC
    assert execution.command.status is ExecutionStatus.READY


def test_approval_required_plan_waits_without_token():
    certified = certificate(
        mode=RecoveryMode.HOLD,
        fallback_strategy=None,
    )

    directive = ContinuityExecutionBridge().build(certified)

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
    )

    assert certified.plan.status is ContinuityStatus.APPROVAL_REQUIRED
    assert directive.approval_token_required is True
    assert execution.command.status is ExecutionStatus.WAITING_APPROVAL
    assert execution.command.attempt_limit == 0


def test_valid_execution_approval_unlocks_directive():
    certified = certificate(
        mode=RecoveryMode.HOLD,
        fallback_strategy=None,
    )
    directive = ContinuityExecutionBridge().build(certified)

    approval = ApprovalToken(
        token_id="approval-136",
        plan_id=directive.plan_id,
        approved_action=directive.action,
        valid_until=500,
        issuer="operator",
    )

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
        approval=approval,
    )

    assert execution.command.status is ExecutionStatus.READY


def test_blocked_plan_remains_rejected_at_execution_boundary():
    certified = certificate(
        mode=RecoveryMode.SAFE_STOP,
        severity=100,
        fallback_strategy=None,
    )

    directive = ContinuityExecutionBridge().build(certified)

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
    )

    assert certified.plan.status is ContinuityStatus.BLOCKED
    assert directive.status == "blocked"
    assert execution.command.status is ExecutionStatus.REJECTED
    assert execution.command.action == "no_op"


def test_bridge_preserves_attempt_limit():
    certified = certificate()

    directive = ContinuityExecutionBridge().build(certified)

    assert directive.max_attempts == certified.plan.max_attempts


def test_bridge_preserves_deadline():
    certified = certificate()

    directive = ContinuityExecutionBridge().build(certified)

    assert directive.deadline == certified.plan.deadline


def test_bridge_links_directive_to_certificate_digest():
    certified = certificate()

    directive = ContinuityExecutionBridge().build(certified)

    assert directive.source_digest == certified.digest
    assert directive.metadata["continuity_digest"] == certified.digest
    assert directive.metadata["recovery_digest"] == certified.recovery_digest


def test_bridge_preserves_plan_identity():
    certified = certificate()

    directive = ContinuityExecutionBridge().build(certified)

    assert directive.plan_id == certified.plan.plan_id
    assert directive.incident_id == certified.plan.incident_id
    assert directive.action == certified.plan.action


def test_tampered_certificate_cannot_cross_execution_bridge():
    certified = certificate()
    tampered = replace(
        certified,
        digest="0" * 64,
    )

    with pytest.raises(
        ValueError,
        match="certificate is invalid",
    ):
        ContinuityExecutionBridge().build(tampered)


def test_empty_bridge_source_is_rejected():
    with pytest.raises(
        ValueError,
        match="source must not be empty",
    ):
        ContinuityExecutionBridge(source="")