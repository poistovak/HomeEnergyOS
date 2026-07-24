from datetime import UTC, datetime, timedelta

import pytest

from heos.calibration import (
    CalibratableParameter,
    CalibrationMetricScales,
    CalibrationMetricWeights,
    CalibrationPolicy,
    CalibrationSample,
    ParameterBounds,
)
from heos.digital_twin import (
    TwinControl,
    TwinDisturbance,
    TwinState,
)


def make_state():
    now = datetime.now(UTC)

    return TwinState(
        observed_at=now,
        indoor_temp_c=22.0,
        battery_soc=0.5,
    )


def make_sample(sample_id="sample-1"):
    return CalibrationSample(
        sample_id=sample_id,
        initial_state=make_state(),
        control=TwinControl(),
        disturbance=TwinDisturbance(
            outdoor_temp_c=20.0,
            pv_kw=5.0,
            base_load_kw=1.0,
        ),
        duration=timedelta(hours=1),
        observed_next_state=TwinState(
            observed_at=datetime.now(UTC) + timedelta(hours=1),
            indoor_temp_c=22.2,
            battery_soc=0.52,
        ),
    )


def test_calibration_sample_accepts_valid_values():
    sample = make_sample()

    assert sample.sample_id == "sample-1"
    assert sample.duration_hours == 1.0


def test_calibration_sample_rejects_empty_id():
    with pytest.raises(ValueError):
        CalibrationSample(
            sample_id="",
            initial_state=make_state(),
            control=TwinControl(),
            disturbance=TwinDisturbance(
                outdoor_temp_c=20.0,
                pv_kw=1.0,
                base_load_kw=1.0,
            ),
            duration=timedelta(hours=1),
            observed_next_state=make_state(),
        )


def test_parameter_bounds_accepts_valid_range():
    bounds = ParameterBounds(
        parameter=CalibratableParameter.HVAC_COP,
        minimum=1.0,
        maximum=5.0,
    )

    assert bounds.minimum == 1.0
    assert bounds.maximum == 5.0


def test_parameter_bounds_rejects_invalid_range():
    with pytest.raises(ValueError):
        ParameterBounds(
            parameter=CalibratableParameter.HVAC_COP,
            minimum=5.0,
            maximum=1.0,
        )


def test_policy_defaults():
    policy = CalibrationPolicy()

    assert policy.rounds == 3
    assert policy.require_validation is False


def test_policy_rejects_invalid_rounds():
    with pytest.raises(ValueError):
        CalibrationPolicy(rounds=0)


def test_metric_weights_accepts_defaults():
    weights = CalibrationMetricWeights()

    assert weights.indoor_temp_c == 1.0


def test_metric_scales_rejects_zero():
    with pytest.raises(ValueError):
        CalibrationMetricScales(
            indoor_temp_c=0.0,
        )


def test_sample_tags_are_normalized():
    sample = CalibrationSample(
        sample_id="abc",
        initial_state=make_state(),
        control=TwinControl(),
        disturbance=TwinDisturbance(
            outdoor_temp_c=20.0,
            pv_kw=1.0,
            base_load_kw=1.0,
        ),
        duration=timedelta(hours=1),
        observed_next_state=TwinState(
            observed_at=datetime.now(UTC) + timedelta(hours=1),
            indoor_temp_c=22.0,
            battery_soc=0.5,
        ),
        tags=("solar", "battery", "solar"),
    )

    assert sample.tags == ("battery", "solar")