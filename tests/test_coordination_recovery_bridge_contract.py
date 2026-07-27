from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from heos.continuity import (
    ContinuityGovernor,
    ContinuityStatus,
    RecoveryMode,
)
from heos.coordination.audit import CoordinationAuditTrail
from heos.coordination.recovery_bridge import CoordinationRecoveryBridge

NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def trail_with_status(
    status: str,
) -> CoordinationAuditTrail:
    trail = CoordinationAuditTrail()

    trail.issue_and_append(
        cycle_id="restart-cycle",
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


def test_empty_audit_recovers_to_safe_stop():
    snapshot = CoordinationRecoveryBridge().build_snapshot(
        CoordinationAuditTrail(),
        now=100,
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert snapshot.severity == 100


def test_rejected_release_recovers_to_safe_stop():
    snapshot = CoordinationRecoveryBridge().build_snapshot(
        trail_with_status("rejected"),
        now=100,
    )

    assert snapshot.mode is RecoveryMode.SAFE_STOP
    assert snapshot.severity == 100


def test_held_release_recovers_to_hold():
    snapshot = CoordinationRecoveryBridge().build_snapshot(
        trail_with_status("held"),
        now=100,
    )

    assert snapshot.mode is RecoveryMode.HOLD


def test_historical_released_state_does_not_resume_execution():
    snapshot = CoordinationRecoveryBridge().build_snapshot(
        trail_with_status("released"),
        now=100,
    )

    assert snapshot.mode is RecoveryMode.HOLD
    assert snapshot.metadata["reason"] == (
        "historical_release_requires_reauthorization"
    )


def test_released_history_requires_continuity_approval():
    snapshot = CoordinationRecoveryBridge().build_snapshot(
        trail_with_status("released"),
        now=100,
    )

    certificate = ContinuityGovernor().govern(
        snapshot,
        now=100,
    )

    assert certificate.plan.status is ContinuityStatus.APPROVAL_REQUIRED
    assert certificate.plan.approval_token_required is True
    assert certificate.plan.action == "maintain_hold"


def test_rejected_history_is_blocked_by_continuity():
    snapshot = CoordinationRecoveryBridge().build_snapshot(
        trail_with_status("rejected"),
        now=100,
    )

    certificate = ContinuityGovernor().govern(
        snapshot,
        now=100,
    )

    assert certificate.plan.status is ContinuityStatus.BLOCKED
    assert certificate.plan.max_attempts == 0


def test_recovery_snapshot_links_to_audit_head():
    trail = trail_with_status("held")
    latest = trail.records()[-1]

    snapshot = CoordinationRecoveryBridge().build_snapshot(
        trail,
        now=100,
    )

    assert snapshot.metadata["audit_digest"] == latest.digest
    assert snapshot.metadata["release_id"] == latest.release_id
    assert snapshot.metadata["cycle_id"] == latest.cycle_id


def test_recovery_expiry_is_bounded_from_restart_time():
    snapshot = CoordinationRecoveryBridge(
        recovery_ttl=120,
    ).build_snapshot(
        trail_with_status("held"),
        now=100,
    )

    assert snapshot.valid_until == 220


def test_negative_now_is_rejected():
    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        CoordinationRecoveryBridge().build_snapshot(
            trail_with_status("held"),
            now=-1,
        )


def test_invalid_recovery_ttl_is_rejected():
    with pytest.raises(
        ValueError,
        match="positive",
    ):
        CoordinationRecoveryBridge(recovery_ttl=0)


def test_tampered_audit_chain_cannot_drive_recovery():
    trail = trail_with_status("released")
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