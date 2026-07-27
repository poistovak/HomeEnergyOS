from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from heos.continuity import (
    ContinuityExecutionBridge,
    ContinuityGovernor,
    ContinuityStatus,
    RecoveryMode,
)
from heos.coordination.audit import CoordinationAuditTrail
from heos.coordination.recovery_bridge import CoordinationRecoveryBridge
from heos.execution_supervisor import (
    ApprovalToken,
    ExecutionStatus,
    ExecutionSupervisor,
)

NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def audit_with_status(
    status: str,
) -> CoordinationAuditTrail:
    trail = CoordinationAuditTrail()

    trail.issue_and_append(
        cycle_id="restart-vertical-slice",
        requested_mode="autonomous",
        effective_mode="autonomous",
        downgraded=False,
        operator_approved=True,
        autonomy_authorized=True,
        release_status=status,
        release_id=f"release-{status}",
        recorded_at=NOW,
    )

    return trail


def recovery_pipeline(
    trail: CoordinationAuditTrail,
    *,
    now: int = 100,
):
    snapshot = CoordinationRecoveryBridge().build_snapshot(
        trail,
        now=now,
    )

    continuity = ContinuityGovernor().govern(
        snapshot,
        now=now,
    )

    directive = ContinuityExecutionBridge().build(
        continuity,
    )

    return snapshot, continuity, directive


def test_historical_release_restarts_in_hold():
    snapshot, continuity, directive = recovery_pipeline(
        audit_with_status("released")
    )

    assert snapshot.mode is RecoveryMode.HOLD
    assert continuity.plan.status is ContinuityStatus.APPROVAL_REQUIRED
    assert directive.approval_token_required is True


def test_historical_release_waits_at_execution_boundary():
    _, _, directive = recovery_pipeline(
        audit_with_status("released")
    )

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
    )

    assert execution.command.status is ExecutionStatus.WAITING_APPROVAL
    assert execution.command.attempt_limit == 0


def test_valid_execution_approval_allows_ready_after_restart():
    _, _, directive = recovery_pipeline(
        audit_with_status("released")
    )

    approval = ApprovalToken(
        token_id="restart-approval",
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
    assert execution.command.attempt_limit > 0


def test_invalid_execution_approval_does_not_unlock_restart():
    _, _, directive = recovery_pipeline(
        audit_with_status("released")
    )

    approval = ApprovalToken(
        token_id="restart-invalid-approval",
        plan_id="wrong-plan",
        approved_action=directive.action,
        valid_until=500,
        issuer="operator",
    )

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
        approval=approval,
    )

    assert execution.command.status is ExecutionStatus.WAITING_APPROVAL
    assert execution.command.attempt_limit == 0


def test_rejected_history_becomes_safe_stop():
    snapshot, continuity, directive = recovery_pipeline(
        audit_with_status("rejected")
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert continuity.plan.status is ContinuityStatus.BLOCKED
    assert directive.status == "blocked"


def test_rejected_history_cannot_reach_ready_execution():
    _, _, directive = recovery_pipeline(
        audit_with_status("rejected")
    )

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
    )

    assert execution.command.status is ExecutionStatus.REJECTED
    assert execution.command.action == "no_op"
    assert execution.command.attempt_limit == 0


def test_empty_history_fails_safe():
    snapshot, continuity, directive = recovery_pipeline(
        CoordinationAuditTrail()
    )

    execution = ExecutionSupervisor().supervise(
        directive,
        now=100,
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert continuity.plan.status is ContinuityStatus.BLOCKED
    assert execution.command.status is ExecutionStatus.REJECTED


def test_restart_chain_preserves_audit_identity():
    trail = audit_with_status("released")
    head = trail.records()[-1]

    snapshot, continuity, directive = recovery_pipeline(
        trail
    )

    assert snapshot.metadata["audit_digest"] == head.digest
    assert snapshot.metadata["release_id"] == head.release_id
    assert directive.metadata["recovery_digest"] == (
        continuity.recovery_digest
    )


def test_tampered_audit_cannot_enter_continuity_pipeline():
    trail = audit_with_status("released")
    original = trail.records()[0]

    trail._records[0] = replace(
        original,
        release_status="rejected",
    )

    assert trail.verify_chain() is False

    with pytest.raises(
        ValueError,
        match="audit chain is invalid",
    ):
        CoordinationRecoveryBridge().build_snapshot(
            trail,
            now=100,
        )


def test_expired_execution_directive_after_restart_is_not_ready():
    _, _, directive = recovery_pipeline(
        audit_with_status("released"),
        now=100,
    )

    execution = ExecutionSupervisor().supervise(
        directive,
        now=directive.deadline + 1,
    )

    assert execution.command.status is ExecutionStatus.EXPIRED


def test_restart_requires_new_execution_certificate():
    _, _, directive = recovery_pipeline(
        audit_with_status("released")
    )

    approval = ApprovalToken(
        token_id="restart-certificate-approval",
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

    assert execution.verify() is True
    assert execution.command.status is ExecutionStatus.READY
    assert execution.directive_digest