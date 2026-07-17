from dataclasses import replace

import pytest

from heos.continuity import (
    ContinuityGovernor,
    ContinuityLedger,
    ContinuityPolicy,
    ContinuityStatus,
    RecoveryMode,
    RecoverySnapshot,
)


def recovery(
    *,
    mode=RecoveryMode.FALLBACK,
    severity=30,
    valid_until=1000,
    fallback_strategy="last_known_safe_plan",
):
    return RecoverySnapshot(
        incident_id="incident-001",
        mode=mode,
        severity=severity,
        fallback_strategy=fallback_strategy,
        valid_until=valid_until,
        metadata={"source": "m24"},
    )


def test_snapshot_validation():
    with pytest.raises(ValueError):
        recovery(severity=101)
    with pytest.raises(ValueError):
        RecoverySnapshot("", RecoveryMode.HOLD, 10, None, 10, {})


def test_fallback_requires_strategy():
    with pytest.raises(ValueError):
        recovery(fallback_strategy=None)


def test_low_severity_is_automatic():
    certificate = ContinuityGovernor().govern(recovery(), now=100)
    assert certificate.plan.status is ContinuityStatus.AUTOMATIC
    assert certificate.plan.max_attempts == 3
    assert not certificate.plan.approval_token_required
    assert certificate.verify()


def test_medium_severity_requires_approval():
    certificate = ContinuityGovernor().govern(
        recovery(severity=60),
        now=100,
    )
    assert certificate.plan.status is ContinuityStatus.APPROVAL_REQUIRED
    assert certificate.plan.approval_token_required


def test_high_severity_requires_approval():
    certificate = ContinuityGovernor().govern(
        recovery(severity=80),
        now=100,
    )
    assert certificate.plan.status is ContinuityStatus.APPROVAL_REQUIRED
    assert certificate.plan.max_attempts == 1


def test_hold_requires_approval():
    certificate = ContinuityGovernor().govern(
        recovery(mode=RecoveryMode.HOLD, fallback_strategy=None),
        now=100,
    )
    assert certificate.plan.action == "maintain_hold"
    assert certificate.plan.status is ContinuityStatus.APPROVAL_REQUIRED


def test_safe_stop_is_blocked():
    certificate = ContinuityGovernor().govern(
        recovery(mode=RecoveryMode.SAFE_STOP, severity=95, fallback_strategy=None),
        now=100,
    )
    assert certificate.plan.status is ContinuityStatus.BLOCKED
    assert certificate.plan.max_attempts == 0
    assert certificate.plan.action == "maintain_safe_stop"


def test_expired_recovery_is_blocked():
    certificate = ContinuityGovernor().govern(
        recovery(valid_until=99),
        now=100,
    )
    assert certificate.plan.status is ContinuityStatus.BLOCKED
    assert certificate.plan.action == "reject_expired_recovery"


def test_deadline_is_bounded_by_recovery_expiry():
    policy = ContinuityPolicy(plan_ttl=500)
    certificate = ContinuityGovernor(policy=policy).govern(
        recovery(valid_until=250),
        now=100,
    )
    assert certificate.plan.deadline == 250


def test_deadline_is_bounded_by_policy_ttl():
    policy = ContinuityPolicy(plan_ttl=50)
    certificate = ContinuityGovernor(policy=policy).govern(
        recovery(valid_until=1000),
        now=100,
    )
    assert certificate.plan.deadline == 150


def test_plan_is_deterministic():
    first = ContinuityGovernor().govern(recovery(), now=100)
    second = ContinuityGovernor().govern(recovery(), now=100)
    assert first.plan.plan_id == second.plan.plan_id
    assert first.digest == second.digest


def test_ledger_chain():
    governor = ContinuityGovernor()
    first = governor.govern(recovery(), now=100)
    second = governor.govern(
        recovery(severity=60),
        now=101,
    )
    assert second.previous_digest == first.digest
    assert governor.ledger.verify_chain()
    assert len(governor.ledger.entries()) == 2


def test_ledger_rejects_wrong_chain():
    first = ContinuityGovernor().govern(recovery(), now=100)
    other = ContinuityGovernor().govern(recovery(severity=60), now=100)
    ledger = ContinuityLedger()
    ledger.append(first)
    with pytest.raises(ValueError):
        ledger.append(other)


def test_tampering_is_detected():
    certificate = ContinuityGovernor().govern(recovery(), now=100)
    tampered = replace(certificate, digest="0" * 64)
    assert not tampered.verify()


def test_policy_validation():
    with pytest.raises(ValueError):
        ContinuityPolicy(automatic_threshold=80, approval_threshold=70)
    with pytest.raises(ValueError):
        ContinuityPolicy(plan_ttl=0)
    with pytest.raises(ValueError):
        ContinuityPolicy(automatic_attempts=-1)


def test_negative_now_rejected():
    with pytest.raises(ValueError):
        ContinuityGovernor().govern(recovery(), now=-1)


def test_json_export():
    certificate = ContinuityGovernor().govern(recovery(), now=100)
    exported = certificate.to_json()
    assert '"policy_version":"25.0.0"' in exported
    assert '"status":"automatic"' in exported
