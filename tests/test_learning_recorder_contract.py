from datetime import UTC, datetime

from heos.result_verification.learning_bridge import LearningBridge
from heos.result_verification.learning_recorder import LearningRecorder
from heos.result_verification.memory import LearningMemory
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


def test_recorder_stores_learning_record():
    memory = LearningMemory()
    recorder = LearningRecorder(memory)

    record = recorder.record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(),
        timestamp=datetime.now(UTC),
    )

    assert record is not None
    assert memory.count() == 1
    assert memory.latest() == record


def test_recorder_returns_stored_record():
    memory = LearningMemory()
    recorder = LearningRecorder(memory)

    record = recorder.record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(),
        timestamp=datetime.now(UTC),
    )

    assert record is not None
    assert record.prediction_id == "pred-001"
    assert record.actual_value == 4900.0


def test_recorder_does_not_store_without_observation():
    memory = LearningMemory()
    recorder = LearningRecorder(memory)

    record = recorder.record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(
            status=VerificationStatus.UNKNOWN,
            observed_value=None,
        ),
        timestamp=datetime.now(UTC),
    )

    assert record is None
    assert memory.count() == 0


def test_recorder_preserves_failed_experience():
    memory = LearningMemory()
    recorder = LearningRecorder(memory)

    record = recorder.record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(
            status=VerificationStatus.FAILED,
            observed_value=4000.0,
        ),
        timestamp=datetime.now(UTC),
    )

    assert record is not None
    assert record.success is False
    assert memory.count() == 1


def test_recorder_can_use_explicit_bridge():
    memory = LearningMemory()
    bridge = LearningBridge()
    recorder = LearningRecorder(
        memory=memory,
        bridge=bridge,
    )

    record = recorder.record(
        prediction_id="pred-001",
        expectation=make_expectation(),
        decision=make_decision(),
        timestamp=datetime.now(UTC),
    )

    assert record is not None
    assert memory.latest() == record