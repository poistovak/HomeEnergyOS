from __future__ import annotations

from dataclasses import replace

import pytest

from heos.continuity import (
    ContinuityGovernor,
    ContinuityStatus,
    RecoveryMode,
)
from heos.execution_supervisor import (
    ContinuityDirective,
    ExecutionLedger,
    ExecutionRestartReconciler,
    ExecutionStatus,
    ExecutionSupervisor,
)


def directive(
    *,
    status: str = "automatic",
    deadline: int = 500,
    approval_token_required: bool = False,
    max_attempts: int = 3,
) -> ContinuityDirective:
    return ContinuityDirective(
        plan_id="plan-restart-138",
        incident_id="incident-restart-138",
        status=status,
        action="apply_safe_recovery",
        max_attempts=max_attempts,
        cooldown_seconds=10,
        deadline=deadline,
        approval_token_required=approval_token_required,
        source_digest="source-138",
        metadata={"source": "test-138"},
    )


def ready_ledger() -> ExecutionLedger:
    supervisor = ExecutionSupervisor()

    certificate = supervisor.supervise(
        directive(),
        now=100,
    )

    assert certificate.command.status is ExecutionStatus.READY

    return supervisor.ledger


def test_empty_execution_history_recovers_to_safe_stop():
    snapshot = ExecutionRestartReconciler().reconcile(
        ExecutionLedger(),
        now=100,
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert snapshot.severity == 100
    assert snapshot.metadata["reason"] == "no_execution_history"


def test_ready_command_does_not_resume_as_ready():
    snapshot = ExecutionRestartReconciler().reconcile(
        ready_ledger(),
        now=100,
    )

    assert snapshot.mode is RecoveryMode.HOLD
    assert snapshot.metadata["reason"] == (
        "ready_command_requires_reauthorization"
    )


def test_ready_command_requires_new_continuity_approval():
    snapshot = ExecutionRestartReconciler().reconcile(
        ready_ledger(),
        now=100,
    )

    continuity = ContinuityGovernor().govern(
        snapshot,
        now=100,
    )

    assert continuity.plan.status is ContinuityStatus.APPROVAL_REQUIRED
    assert continuity.plan.approval_token_required is True


def test_ready_command_expired_during_restart_fails_safe():
    snapshot = ExecutionRestartReconciler().reconcile(
        ready_ledger(),
        now=501,
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert snapshot.metadata["reason"] == (
        "ready_command_expired_during_restart"
    )


def test_waiting_approval_stays_in_hold_after_restart():
    supervisor = ExecutionSupervisor()

    certificate = supervisor.supervise(
        directive(
            status="approval_required",
            approval_token_required=True,
        ),
        now=100,
    )

    assert certificate.command.status is ExecutionStatus.WAITING_APPROVAL

    snapshot = ExecutionRestartReconciler().reconcile(
        supervisor.ledger,
        now=100,
    )

    assert snapshot.mode is RecoveryMode.HOLD
    assert snapshot.metadata["reason"] == (
        "approval_must_be_revalidated_after_restart"
    )


def test_rejected_execution_recovers_to_safe_stop():
    supervisor = ExecutionSupervisor()

    certificate = supervisor.supervise(
        directive(
            status="blocked",
            max_attempts=0,
        ),
        now=100,
    )

    assert certificate.command.status is ExecutionStatus.REJECTED

    snapshot = ExecutionRestartReconciler().reconcile(
        supervisor.ledger,
        now=100,
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert snapshot.metadata["reason"] == "last_execution_rejected"


def test_reconciliation_links_to_execution_certificate():
    ledger = ready_ledger()
    latest = ledger.entries()[-1]

    snapshot = ExecutionRestartReconciler().reconcile(
        ledger,
        now=100,
    )

    assert snapshot.metadata["execution_certificate_digest"] == latest.digest
    assert snapshot.metadata["command_id"] == latest.command.command_id
    assert snapshot.metadata["plan_id"] == latest.command.plan_id
    assert snapshot.metadata["directive_digest"] == latest.directive_digest


def test_recovery_ttl_is_bounded_from_restart_time():
    snapshot = ExecutionRestartReconciler(
        recovery_ttl=120,
    ).reconcile(
        ready_ledger(),
        now=100,
    )

    assert snapshot.valid_until == 220


def test_tampered_execution_ledger_cannot_drive_recovery():
    ledger = ready_ledger()
    original = ledger.entries()[0]

    ledger._entries[0] = replace(
        original,
        digest="0" * 64,
    )

    assert ledger.verify_chain() is False

    with pytest.raises(
        ValueError,
        match="execution ledger chain is invalid",
    ):
        ExecutionRestartReconciler().reconcile(
            ledger,
            now=100,
        )


def test_negative_restart_time_is_rejected():
    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        ExecutionRestartReconciler().reconcile(
            ready_ledger(),
            now=-1,
        )


def test_invalid_recovery_ttl_is_rejected():
    with pytest.raises(
        ValueError,
        match="positive",
    ):
        ExecutionRestartReconciler(
            recovery_ttl=0,
        )