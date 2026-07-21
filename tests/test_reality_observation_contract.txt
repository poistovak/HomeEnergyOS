from datetime import UTC, datetime

import pytest

from heos.result_verification import Observation


def make_observation():
    return Observation(
        target="pv_power_w",
        value=5900.0,
        observed_at=datetime.now(UTC),
        source="home_sensor",
    )


def test_observation_accepts_valid_values():
    observation = make_observation()

    assert observation.target == "pv_power_w"
    assert observation.value == 5900.0
    assert observation.source == "home_sensor"


def test_observation_rejects_empty_target():
    with pytest.raises(ValueError):
        Observation(
            target="",
            value=100.0,
            observed_at=datetime.now(UTC),
            source="sensor",
        )


def test_observation_rejects_empty_source():
    with pytest.raises(ValueError):
        Observation(
            target="pv_power_w",
            value=100.0,
            observed_at=datetime.now(UTC),
            source="",
        )


def test_observation_requires_timezone():
    with pytest.raises(ValueError):
        Observation(
            target="pv_power_w",
            value=100.0,
            observed_at=datetime.now(),
            source="sensor",
        )