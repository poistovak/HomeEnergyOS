from __future__ import annotations

from dataclasses import replace

import pytest

from heos.continuity import ContinuityGovernor, ContinuityStatus, RecoveryMode
from heos.execution_supervisor import ExecutionOutcomeReconciler
from heos.outcome_verifier import (
    ExecutionEvidence,
    ExpectedOutcome,
    OutcomeStatus,
    OutcomeVerifier,
)


def expected() -> ExpectedOutcome:
    return ExpectedOutcome(
        command_id="cmd-139",
        incident_id="incident-139",
        metric="grid_power",
        target_min=-50.0,
        target_max=50.0,
        deadline=500,
        source_digest="execution-139",
    )


def evidence(
    *,
    values: dict[str, float] | None = None,
    observed_at: int = 200,
) -> ExecutionEvidence:
    return ExecutionEvidence(
        command_id="cmd-139",
        observed_at=observed_at,
        values={"grid_power": 10.0} if values is None else values,
        attempts_used=1,
        executor="home_assistant",
    )


def outcome(
    *,
    values: dict[str, float] | None = None,
):
    return OutcomeVerifier().verify_outcome(
        expected(),
        evidence(values=values),
    )


def test_verified_outcome_never_requests_replay():
    certificate = outcome()

    assert certificate.result.status is OutcomeStatus.VERIFIED

    snapshot = ExecutionOutcomeReconciler().reconcile(
        certificate,
        now=300,
    )

    assert snapshot.mode is RecoveryMode.HOLD
    assert snapshot.metadata["reason"] == (
        "execution_already_verified_no_replay"
    )


def test_verified_outcome_is_not_automatic_continuity():
    snapshot = ExecutionOutcomeReconciler().reconcile(
        outcome(),
        now=300,
    )

    continuity = ContinuityGovernor().govern(
        snapshot,
        now=300,
    )

    assert continuity.plan.status is ContinuityStatus.APPROVAL_REQUIRED


def test_inconclusive_outcome_stays_in_hold():
    certificate = outcome(values={})

    assert certificate.result.status is OutcomeStatus.INCONCLUSIVE

    snapshot = ExecutionOutcomeReconciler().reconcile(
        certificate,
        now=300,
    )

    assert snapshot.mode is RecoveryMode.HOLD
    assert snapshot.metadata["reason"] == (
        "execution_outcome_inconclusive_no_replay"
    )


def test_inconclusive_is_not_treated_as_not_executed():
    snapshot = ExecutionOutcomeReconciler().reconcile(
        outcome(values={}),
        now=300,
    )

    continuity = ContinuityGovernor().govern(
        snapshot,
        now=300,
    )

    assert continuity.plan.status is ContinuityStatus.APPROVAL_REQUIRED
    assert continuity.plan.approval_token_required is True


def test_degraded_outcome_requires_hold():
    certificate = outcome(
        values={"grid_power": 54.0},
    )

    assert certificate.result.status is OutcomeStatus.DEGRADED

    snapshot = ExecutionOutcomeReconciler().reconcile(
        certificate,
        now=300,
    )

    assert snapshot.mode is RecoveryMode.HOLD


def test_failed_outcome_fails_safe():
    certificate = outcome(
        values={"grid_power": 100.0},
    )

    assert certificate.result.status is OutcomeStatus.FAILED

    snapshot = ExecutionOutcomeReconciler().reconcile(
        certificate,
        now=300,
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert snapshot.metadata["reason"] == "execution_outcome_failed"


def test_failed_outcome_is_blocked_by_continuity():
    snapshot = ExecutionOutcomeReconciler().reconcile(
        outcome(values={"grid_power": 100.0}),
        now=300,
    )

    continuity = ContinuityGovernor().govern(
        snapshot,
        now=300,
    )

    assert continuity.plan.status is ContinuityStatus.BLOCKED


def test_reconciliation_links_to_outcome_certificate():
    certificate = outcome()

    snapshot = ExecutionOutcomeReconciler().reconcile(
        certificate,
        now=300,
    )

    assert snapshot.metadata["outcome_certificate_digest"] == (
        certificate.digest
    )
    assert snapshot.metadata["result_id"] == certificate.result.result_id
    assert snapshot.metadata["command_id"] == certificate.result.command_id


def test_tampered_outcome_certificate_cannot_drive_recovery():
    certificate = outcome()

    tampered = replace(
        certificate,
        digest="0" * 64,
    )

    with pytest.raises(
        ValueError,
        match="outcome certificate is invalid",
    ):
        ExecutionOutcomeReconciler().reconcile(
            tampered,
            now=300,
        )


def test_negative_now_is_rejected():
    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        ExecutionOutcomeReconciler().reconcile(
            outcome(),
            now=-1,
        )


def test_invalid_recovery_ttl_is_rejected():
    with pytest.raises(
        ValueError,
        match="positive",
    ):
        ExecutionOutcomeReconciler(
            recovery_ttl=0,
        )