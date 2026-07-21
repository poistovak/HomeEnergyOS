import pytest

from heos.result_verification import ResultExpectation


class ForecastVerificationRequest:
    def __init__(
        self,
        forecast_id: str,
        target: str,
        predicted_value: float,
        tolerance: float,
    ):
        self.forecast_id = forecast_id
        self.target = target
        self.predicted_value = predicted_value
        self.tolerance = tolerance

        if not forecast_id.strip():
            raise ValueError("forecast_id empty")

        if not target.strip():
            raise ValueError("target empty")

        if tolerance < 0:
            raise ValueError("tolerance negative")

        if predicted_value != predicted_value:
            raise ValueError("predicted_value invalid")

    def to_expectation(self) -> ResultExpectation:
        return ResultExpectation(
            command_id=self.forecast_id,
            target=self.target,
            expected_value=self.predicted_value,
            absolute_tolerance=self.tolerance,
        )


def test_forecast_request_creates_expectation():
    request = ForecastVerificationRequest(
        forecast_id="forecast-001",
        target="pv_power_kw",
        predicted_value=6.2,
        tolerance=0.5,
    )

    expectation = request.to_expectation()

    assert expectation.command_id == "forecast-001"
    assert expectation.target == "pv_power_kw"
    assert expectation.expected_value == 6.2


def test_forecast_request_rejects_empty_id():
    with pytest.raises(ValueError):
        ForecastVerificationRequest(
            forecast_id="",
            target="pv_power_kw",
            predicted_value=5.0,
            tolerance=0.5,
        )


def test_forecast_request_rejects_negative_tolerance():
    with pytest.raises(ValueError):
        ForecastVerificationRequest(
            forecast_id="forecast-001",
            target="pv_power_kw",
            predicted_value=5.0,
            tolerance=-1.0,
        )


def test_forecast_request_rejects_nan_prediction():
    with pytest.raises(ValueError):
        ForecastVerificationRequest(
            forecast_id="forecast-001",
            target="pv_power_kw",
            predicted_value=float("nan"),
            tolerance=0.5,
        )