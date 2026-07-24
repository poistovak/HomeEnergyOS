import pytest

from heos.result_verification import (
    Observation,
    ResultExpectation,
    ResultVerificationEngine,
    ResultVerificationPolicy,
    ResultVerifier,
    VerificationAction,
    VerificationStatus,
)


def expectation(**changes):
    values = {
        "command_id": "cmd-028",
        "target": "wattpilot.charging_power",
        "expected_value": 2300.0,
        "absolute_tolerance": 250.0,
        "relative_tolerance": 0.0,
        "deadline": 20,
        "stability_samples": 2,
        "minimum_samples": 2,
        "rollback_supported": True,
    }
    values.update(changes)
    return ResultExpectation(**values)


def observation(value=2300.0, observed_at=10, **changes):
    values = {
        "target": "wattpilot.charging_power",
        "value": value,
        "observed_at": observed_at,
        "source": "home_assistant",
        "quality": 1.0,
    }
    values.update(changes)
    return Observation(**values)


def test_success_after_stable_target_samples():
    result = ResultVerifier().verify(
        expectation(),
        [observation(2250, 8), observation(2310, 10)],
    )
    assert result.status is VerificationStatus.SUCCESS
    assert result.action is VerificationAction.ACCEPT
    assert result.stable_samples == 2


def test_partial_when_only_one_stable_sample_exists():
    result = ResultVerifier().verify(expectation(), [observation(2290, 10)])
    assert result.status is VerificationStatus.PARTIAL
    assert result.action is VerificationAction.RETRY


def test_partial_when_value_is_inside_extended_tolerance():
    result = ResultVerifier().verify(
        expectation(stability_samples=1, minimum_samples=1),
        [observation(2700, 10)],
    )
    assert result.status is VerificationStatus.PARTIAL


def test_failed_when_value_is_far_from_target():
    result = ResultVerifier().verify(expectation(), [observation(0, 10)])
    assert result.status is VerificationStatus.FAILED
    assert result.action is VerificationAction.ROLLBACK


def test_unknown_without_observations_before_deadline():
    result = ResultVerifier().verify(expectation(), [], now=10)
    assert result.status is VerificationStatus.UNKNOWN
    assert result.action is VerificationAction.RETRY


def test_timeout_without_observations_after_deadline():
    result = ResultVerifier().verify(expectation(), [], now=21)
    assert result.status is VerificationStatus.TIMEOUT


def test_late_observation_times_out():
    result = ResultVerifier().verify(expectation(), [observation(2300, 21)])
    assert result.status is VerificationStatus.TIMEOUT


def test_wrong_target_is_ignored():
    result = ResultVerifier().verify(
        expectation(),
        [observation(target="battery.power")],
        now=10,
    )
    assert result.status is VerificationStatus.UNKNOWN


def test_low_quality_observation_is_ignored():
    result = ResultVerifier().verify(
        expectation(),
        [observation(quality=0.2)],
        now=10,
    )
    assert result.status is VerificationStatus.UNKNOWN


def test_relative_tolerance_is_supported():
    result = ResultVerifier().verify(
        expectation(
            expected_value=1000,
            absolute_tolerance=0,
            relative_tolerance=0.1,
            stability_samples=1,
            minimum_samples=1,
        ),
        [observation(1090)],
    )
    assert result.status is VerificationStatus.SUCCESS


def test_absolute_tolerance_wins_when_larger():
    exp = expectation(expected_value=1000, absolute_tolerance=200, relative_tolerance=0.1)
    assert exp.effective_tolerance == 200


def test_observations_are_sorted_by_timestamp():
    result = ResultVerifier().verify(
        expectation(stability_samples=2),
        [observation(2300, 10), observation(0, 1), observation(2300, 9)],
    )
    assert result.status is VerificationStatus.SUCCESS


def test_trailing_stability_resets_after_bad_latest_sample():
    result = ResultVerifier().verify(
        expectation(),
        [observation(2300, 8), observation(2300, 9), observation(0, 10)],
    )
    assert result.stable_samples == 0
    assert result.status is VerificationStatus.FAILED


def test_retry_limit_escalates_partial_result():
    verifier = ResultVerifier(ResultVerificationPolicy(retry_limit=2))
    result = verifier.verify(expectation(), [observation(2300)], attempts_used=2)
    assert result.action is VerificationAction.ESCALATE


def test_timeout_rolls_back_after_retry_limit():
    verifier = ResultVerifier(ResultVerificationPolicy(retry_limit=1))
    result = verifier.verify(expectation(), [], attempts_used=1, now=21)
    assert result.action is VerificationAction.ROLLBACK


def test_failure_retries_when_rollback_is_not_supported():
    result = ResultVerifier().verify(
        expectation(rollback_supported=False),
        [observation(0)],
    )
    assert result.action is VerificationAction.RETRY


def test_failure_escalates_without_rollback_after_retry_limit():
    verifier = ResultVerifier(ResultVerificationPolicy(retry_limit=1))
    result = verifier.verify(
        expectation(rollback_supported=False),
        [observation(0)],
        attempts_used=1,
    )
    assert result.action is VerificationAction.ESCALATE


def test_engine_records_decisions():
    engine = ResultVerificationEngine()
    result = engine.verify(expectation(), [observation(2250, 8), observation(2300, 9)])
    assert engine.ledger.entries() == (result,)
    assert engine.ledger.latest_for("cmd-028") == result


def test_ledger_deduplicates_identical_decision():
    engine = ResultVerificationEngine()
    first = engine.verify(expectation(), [observation(2250, 8), observation(2300, 9)])
    second = engine.verify(expectation(), [observation(2250, 8), observation(2300, 9)])
    assert first.verification_id == second.verification_id
    assert len(engine.ledger.entries()) == 1


def test_decision_is_deterministic():
    verifier = ResultVerifier()
    first = verifier.verify(expectation(), [observation(2250, 8), observation(2300, 9)])
    second = verifier.verify(expectation(), [observation(2250, 8), observation(2300, 9)])
    assert first.verification_id == second.verification_id


def test_json_export_contains_status_and_action():
    result = ResultVerifier().verify(
        expectation(),
        [observation(2250, 8), observation(2300, 9)],
    )
    exported = result.to_json()
    assert '"status":"success"' in exported
    assert '"action":"accept"' in exported


def test_negative_attempt_count_is_rejected():
    with pytest.raises(ValueError):
        ResultVerifier().verify(expectation(), [], attempts_used=-1)


def test_model_validation():
    with pytest.raises(ValueError):
        expectation(command_id="")
    with pytest.raises(ValueError):
        expectation(absolute_tolerance=-1)
    with pytest.raises(ValueError):
        expectation(stability_samples=0)
    with pytest.raises(ValueError):
        observation(quality=1.1)


def test_policy_validation():
    with pytest.raises(ValueError):
        ResultVerificationPolicy(retry_limit=-1)
    with pytest.raises(ValueError):
        ResultVerificationPolicy(partial_multiplier=0.5)
    with pytest.raises(ValueError):
        ResultVerificationPolicy(minimum_quality=2.0)


def test_zero_expected_value_has_safe_relative_error():
    result = ResultVerifier().verify(
        expectation(
            expected_value=0,
            absolute_tolerance=1,
            stability_samples=1,
            minimum_samples=1,
        ),
        [observation(0.5)],
    )
    assert result.relative_error == 0.5
