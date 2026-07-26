from datetime import UTC, datetime

import pytest

from heos.result_verification.learning_bridge import LearningBridge
from heos.result_verification.models import (
    ResultExpectation,
    VerificationAction,
    VerificationDecision,
    VerificationStatus,
)


def make_expectation() -> ResultExpectation:
    return ResultExpectation(
        command_id="cmd-001",
        target="pv_power_w",
        expected_value=5000.0,
        absolute_tolerance=100.0,
        relative_tolerance=0.05,
        deadline=100,
        stability_samples=1,
        minimum_samples=1,
        rollback_supported=True,
    )


def make_decision(
    *,
    status: VerificationStatus = VerificationStatus.SUCCESS,
    observed_value: float | None = 4900.0,
) -> VerificationDecision:
    return VerificationDecision.create(
        command_id="cmd-001",
        target="pv_power_w",
        status=status,
        action=VerificationAction.ACCEPT,
        expected_value=5000.0,
        observed_value=observed_value,
        absolute_error=(
            None
            if observed_value is None
            else abs(observed_value - 5000.0)
        ),
        relative_error=(
            None
            if observed_value is None
            else abs(observed_value - 5000.0) / 5000.0
        ),
        stable_samples=1 if observed_value is not None else 0,
        evidence_count=1 if observed_value is not None else 0,
        attempts_used=0,
        reasons=("verification completed",),
        policy_version="1.0",
    )


def test_bridge_creates_learning_record_from_success():
    bridge = LearningBridge()

    record = bridge.build_record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(),
        timestamp=datetime.now(UTC),
    )

    assert record is not None
    assert record.prediction_id == "pred-001"
    assert record.command_id == "cmd-001"
    assert record.expected_value == 5000.0
    assert record.actual_value == 4900.0
    assert record.success is True


def test_bridge_marks_failed_verification_as_unsuccessful():
    bridge = LearningBridge()

    record = bridge.build_record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(
            status=VerificationStatus.FAILED,
            observed_value=4200.0,
        ),
        timestamp=datetime.now(UTC),
    )

    assert record is not None
    assert record.actual_value == 4200.0
    assert record.success is False


def test_bridge_does_not_learn_without_observation():
    bridge = LearningBridge()

    record = bridge.build_record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(
            status=VerificationStatus.UNKNOWN,
            observed_value=None,
        ),
        timestamp=datetime.now(UTC),
    )

    assert record is None


def test_bridge_requires_prediction_id():
    bridge = LearningBridge()

    with pytest.raises(ValueError):
        bridge.build_record(
            prediction_id="",
            expectation=make_expectation(),
            decision=make_decision(),
            timestamp=datetime.now(UTC),
        )


def test_bridge_requires_timezone_aware_timestamp():
    bridge = LearningBridge()

    with pytest.raises(ValueError):
        bridge.build_record(
            prediction_id="pred-001",
            expectation=make_expectation(),
            decision=make_decision(),
            timestamp=datetime.now(),
        )


def test_bridge_rejects_mismatched_command():
    bridge = LearningBridge()

    decision = VerificationDecision.create(
        command_id="cmd-other",
        target="pv_power_w",
        status=VerificationStatus.SUCCESS,
        action=VerificationAction.ACCEPT,
        expected_value=5000.0,
        observed_value=4900.0,
        absolute_error=100.0,
        relative_error=0.02,
        stable_samples=1,
        evidence_count=1,
        attempts_used=0,
        reasons=("verification completed",),
        policy_version="1.0",
    )

    with pytest.raises(ValueError):
        bridge.build_record(
            prediction_id="pred-001",
            expectation=make_expectation(),
            decision=decision,
            timestamp=datetime.now(UTC),
        )


def test_bridge_rejects_mismatched_target():
    bridge = LearningBridge()

    decision = VerificationDecision.create(
        command_id="cmd-001",
        target="battery_power_w",
        status=VerificationStatus.SUCCESS,
        action=VerificationAction.ACCEPT,
        expected_value=5000.0,
        observed_value=4900.0,
        absolute_error=100.0,
        relative_error=0.02,
        stable_samples=1,
        evidence_count=1,
        attempts_used=0,
        reasons=("verification completed",),
        policy_version="1.0",
    )

    with pytest.raises(ValueError):
        bridge.build_record(
            prediction_id="pred-001",
            expectation=make_expectation(),
            decision=decision,
            timestamp=datetime.now(UTC),
        )