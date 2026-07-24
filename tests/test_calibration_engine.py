from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from heos.calibration import (
    CalibratableParameter,
    CalibrationConfigurationError,
    CalibrationConflictError,
    CalibrationMetricScales,
    CalibrationMetricWeights,
    CalibrationNotFoundError,
    CalibrationPolicy,
    CalibrationReport,
    CalibrationSample,
    DigitalTwinCalibrator,
    InMemoryCalibrationRepository,
    JsonlCalibrationRepository,
    ParameterBounds,
    ParameterEstimate,
    dumps_report,
    evaluate_parameters,
    loads_report,
)
from heos.digital_twin import DigitalTwin, TwinControl, TwinDisturbance, TwinParameters, TwinState

NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


def parameters(**overrides: float | str) -> TwinParameters:
    values: dict[str, float | str] = {
        "thermal_capacity_kwh_per_c": 10.0,
        "heat_loss_kw_per_c": 0.2,
        "hvac_cop": 4.0,
        "battery_capacity_kwh": 10.0,
        "battery_max_charge_kw": 20.0,
        "battery_max_discharge_kw": 20.0,
        "battery_charge_efficiency": 1.0,
        "battery_discharge_efficiency": 1.0,
        "ev_capacity_kwh": 20.0,
        "ev_max_charge_kw": 20.0,
        "ev_charge_efficiency": 1.0,
        "grid_max_import_kw": 100.0,
        "grid_max_export_kw": 100.0,
        "indoor_min_c": -50.0,
        "indoor_max_c": 50.0,
        "version": "base-1",
    }
    values.update(overrides)
    return TwinParameters(**values)  # type: ignore[arg-type]


def state(**overrides: float | datetime) -> TwinState:
    values: dict[str, float | datetime] = {
        "observed_at": NOW,
        "indoor_temp_c": 20.0,
        "battery_soc": 0.5,
        "ev_soc": 0.2,
        "grid_import_kwh": 0.0,
        "grid_export_kwh": 0.0,
        "battery_throughput_kwh": 0.0,
    }
    values.update(overrides)
    return TwinState(**values)  # type: ignore[arg-type]


def disturbance(**overrides: float) -> TwinDisturbance:
    values = {
        "outdoor_temp_c": 10.0,
        "pv_kw": 0.0,
        "base_load_kw": 1.0,
        "solar_gain_kw": 0.0,
        "internal_gain_kw": 0.0,
    }
    values.update(overrides)
    return TwinDisturbance(**values)


def sample_from(
    true_parameters: TwinParameters,
    *,
    sample_id: str = "sample-1",
    initial: TwinState | None = None,
    control: TwinControl | None = None,
    weather: TwinDisturbance | None = None,
    duration: timedelta = HOUR,
    weight: float = 1.0,
) -> CalibrationSample:
    initial = initial or state()
    control = control or TwinControl()
    weather = weather or disturbance()
    observed = DigitalTwin(true_parameters).step(
        initial,
        control,
        weather,
        duration=duration,
    ).next_state
    return CalibrationSample(
        sample_id=sample_id,
        initial_state=initial,
        control=control,
        disturbance=weather,
        duration=duration,
        observed_next_state=observed,
        weight=weight,
    )


def only_weight(name: str) -> CalibrationMetricWeights:
    values = {field: 0.0 for field in CalibrationMetricWeights.__dataclass_fields__}
    values[name] = 1.0
    return CalibrationMetricWeights(**values)


def calibrate_one(
    base: TwinParameters,
    true: TwinParameters,
    parameter: CalibratableParameter,
    minimum: float,
    maximum: float,
    *,
    samples: tuple[CalibrationSample, ...],
    weight_name: str,
) -> CalibrationReport:
    policy = CalibrationPolicy(
        rounds=2,
        minimum_absolute_improvement=0.0,
        minimum_relative_improvement=0.0,
        weights=only_weight(weight_name),
    )
    return DigitalTwinCalibrator(policy).calibrate(
        base,
        samples,
        [ParameterBounds(parameter, minimum, maximum, candidates=5)],
        generated_at=NOW,
    )


def test_sample_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="sample_id"):
        sample_from(parameters(), sample_id=" ")


def test_sample_rejects_zero_duration() -> None:
    with pytest.raises(ValueError, match="duration"):
        CalibrationSample(
            sample_id="sample-zero",
            initial_state=state(),
            control=TwinControl(),
            disturbance=disturbance(),
            duration=timedelta(0),
            observed_next_state=state(observed_at=NOW + HOUR),
        )


def test_sample_rejects_negative_weight() -> None:
    with pytest.raises(ValueError, match="weight"):
        sample_from(parameters(), weight=-1.0)


def test_sample_normalizes_tags() -> None:
    base = sample_from(parameters())
    item = replace(base, tags=(" winter ", "solar", "solar"))
    assert item.tags == ("solar", "winter")


def test_bounds_reject_equal_limits() -> None:
    with pytest.raises(ValueError, match="maximum"):
        ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 2.0)


def test_bounds_reject_even_candidate_count() -> None:
    with pytest.raises(ValueError, match="odd"):
        ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0, candidates=4)


def test_fraction_bounds_reject_above_one() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        ParameterBounds(
            CalibratableParameter.BATTERY_CHARGE_EFFICIENCY,
            0.5,
            1.1,
        )


def test_weights_require_positive_metric() -> None:
    with pytest.raises(ValueError, match="at least one"):
        CalibrationMetricWeights(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_scales_require_positive_values() -> None:
    with pytest.raises(ValueError, match="indoor_temp_c"):
        CalibrationMetricScales(indoor_temp_c=0.0)


def test_policy_rejects_zero_rounds() -> None:
    with pytest.raises(ValueError, match="rounds"):
        CalibrationPolicy(rounds=0)


def test_policy_rejects_relative_improvement_above_one() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        CalibrationPolicy(minimum_relative_improvement=1.1)


def test_evaluate_perfect_parameters_has_zero_loss() -> None:
    true = parameters(thermal_capacity_kwh_per_c=20.0)
    samples = (sample_from(true, control=TwinControl(hvac_thermal_kw=4.0)),)
    metrics = evaluate_parameters(
        true,
        samples,
        weights=CalibrationMetricWeights(),
        scales=CalibrationMetricScales(),
    )
    assert metrics.weighted_loss == pytest.approx(0.0)


def test_evaluate_rejects_empty_samples() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        evaluate_parameters(
            parameters(),
            (),
            weights=CalibrationMetricWeights(),
            scales=CalibrationMetricScales(),
        )


def test_evaluate_uses_sample_weights() -> None:
    true = parameters(thermal_capacity_kwh_per_c=20.0)
    first = sample_from(true, sample_id="a", control=TwinControl(hvac_thermal_kw=4.0), weight=10.0)
    second = sample_from(parameters(), sample_id="b", control=TwinControl(hvac_thermal_kw=4.0), weight=1.0)
    metrics = evaluate_parameters(
        parameters(),
        (first, second),
        weights=only_weight("indoor_temp_c"),
        scales=CalibrationMetricScales(),
    )
    assert metrics.indoor_temp_mae_c > 0.0
    assert metrics.total_weight == 11.0


def test_calibrator_rejects_naive_generated_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        DigitalTwinCalibrator().calibrate(
            parameters(),
            [sample_from(parameters())],
            [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
            generated_at=datetime(2026, 7, 15, 9),
        )


def test_calibrator_rejects_empty_bounds() -> None:
    with pytest.raises(CalibrationConfigurationError, match="bounds"):
        DigitalTwinCalibrator().calibrate(
            parameters(),
            [sample_from(parameters())],
            [],
            generated_at=NOW,
        )


def test_calibrator_rejects_duplicate_bounds() -> None:
    bound = ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)
    with pytest.raises(CalibrationConfigurationError, match="only once"):
        DigitalTwinCalibrator().calibrate(
            parameters(),
            [sample_from(parameters())],
            [bound, bound],
            generated_at=NOW,
        )


def test_calibrator_rejects_base_outside_bounds() -> None:
    with pytest.raises(CalibrationConfigurationError, match="inside"):
        DigitalTwinCalibrator().calibrate(
            parameters(hvac_cop=4.0),
            [sample_from(parameters())],
            [ParameterBounds(CalibratableParameter.HVAC_COP, 1.0, 3.0)],
            generated_at=NOW,
        )


def test_calibrator_rejects_duplicate_sample_ids() -> None:
    item = sample_from(parameters())
    with pytest.raises(ValueError, match="unique"):
        DigitalTwinCalibrator().calibrate(
            parameters(),
            [item, item],
            [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
            generated_at=NOW,
        )


def test_calibrator_rejects_train_validation_overlap() -> None:
    item = sample_from(parameters())
    with pytest.raises(CalibrationConfigurationError, match="must not overlap"):
        DigitalTwinCalibrator().calibrate(
            parameters(),
            [item],
            [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
            generated_at=NOW,
            validation_samples=[item],
        )


def test_policy_can_require_validation() -> None:
    with pytest.raises(CalibrationConfigurationError, match="required"):
        DigitalTwinCalibrator(CalibrationPolicy(require_validation=True)).calibrate(
            parameters(),
            [sample_from(parameters())],
            [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
            generated_at=NOW,
        )


def test_calibrates_thermal_capacity() -> None:
    base = parameters(thermal_capacity_kwh_per_c=10.0)
    true = parameters(thermal_capacity_kwh_per_c=20.0)
    samples = (
        sample_from(true, sample_id="a", control=TwinControl(hvac_thermal_kw=4.0)),
        sample_from(true, sample_id="b", initial=state(indoor_temp_c=22.0), control=TwinControl()),
    )
    report = calibrate_one(base, true, CalibratableParameter.THERMAL_CAPACITY_KWH_PER_C, 5.0, 25.0, samples=samples, weight_name="indoor_temp_c")
    assert report.calibrated_parameters.thermal_capacity_kwh_per_c == pytest.approx(20.0)


def test_calibrates_heat_loss() -> None:
    base = parameters(heat_loss_kw_per_c=0.2)
    true = parameters(heat_loss_kw_per_c=0.4)
    samples = (
        sample_from(true, sample_id="a", initial=state(indoor_temp_c=22.0), weather=disturbance(outdoor_temp_c=5.0)),
        sample_from(true, sample_id="b", initial=state(indoor_temp_c=19.0), weather=disturbance(outdoor_temp_c=12.0)),
    )
    report = calibrate_one(base, true, CalibratableParameter.HEAT_LOSS_KW_PER_C, 0.1, 0.5, samples=samples, weight_name="indoor_temp_c")
    assert report.calibrated_parameters.heat_loss_kw_per_c == pytest.approx(0.4)


def test_calibrates_hvac_cop_from_grid_energy() -> None:
    base = parameters(hvac_cop=4.0)
    true = parameters(hvac_cop=2.0)
    samples = (
        sample_from(true, sample_id="a", control=TwinControl(hvac_thermal_kw=4.0)),
        sample_from(true, sample_id="b", control=TwinControl(hvac_thermal_kw=8.0)),
    )
    report = calibrate_one(base, true, CalibratableParameter.HVAC_COP, 2.0, 6.0, samples=samples, weight_name="grid_import_kwh")
    assert report.calibrated_parameters.hvac_cop == pytest.approx(2.0)


def test_calibrates_battery_capacity() -> None:
    base = parameters(battery_capacity_kwh=10.0)
    true = parameters(battery_capacity_kwh=20.0)
    samples = (
        sample_from(true, sample_id="a", control=TwinControl(battery_power_kw=4.0)),
        sample_from(true, sample_id="b", initial=state(battery_soc=0.8), control=TwinControl(battery_power_kw=-4.0)),
    )
    report = calibrate_one(base, true, CalibratableParameter.BATTERY_CAPACITY_KWH, 5.0, 25.0, samples=samples, weight_name="battery_soc")
    assert report.calibrated_parameters.battery_capacity_kwh == pytest.approx(20.0)


def test_calibrates_battery_charge_efficiency() -> None:
    base = parameters(battery_charge_efficiency=1.0)
    true = parameters(battery_charge_efficiency=0.8)
    samples = (
        sample_from(true, sample_id="a", control=TwinControl(battery_power_kw=2.0)),
        sample_from(true, sample_id="b", control=TwinControl(battery_power_kw=4.0)),
    )
    report = calibrate_one(base, true, CalibratableParameter.BATTERY_CHARGE_EFFICIENCY, 0.6, 1.0, samples=samples, weight_name="battery_soc")
    assert report.calibrated_parameters.battery_charge_efficiency == pytest.approx(0.8)


def test_calibrates_battery_discharge_efficiency() -> None:
    base = parameters(battery_discharge_efficiency=1.0)
    true = parameters(battery_discharge_efficiency=0.8)
    samples = (
        sample_from(true, sample_id="a", control=TwinControl(battery_power_kw=-2.0)),
        sample_from(true, sample_id="b", initial=state(battery_soc=0.8), control=TwinControl(battery_power_kw=-4.0)),
    )
    report = calibrate_one(base, true, CalibratableParameter.BATTERY_DISCHARGE_EFFICIENCY, 0.6, 1.0, samples=samples, weight_name="battery_soc")
    assert report.calibrated_parameters.battery_discharge_efficiency == pytest.approx(0.8)


def test_calibrates_ev_capacity() -> None:
    base = parameters(ev_capacity_kwh=20.0)
    true = parameters(ev_capacity_kwh=40.0)
    samples = (
        sample_from(true, sample_id="a", control=TwinControl(ev_charge_kw=4.0)),
        sample_from(true, sample_id="b", control=TwinControl(ev_charge_kw=8.0)),
    )
    report = calibrate_one(base, true, CalibratableParameter.EV_CAPACITY_KWH, 10.0, 50.0, samples=samples, weight_name="ev_soc")
    assert report.calibrated_parameters.ev_capacity_kwh == pytest.approx(40.0)


def test_calibrates_ev_efficiency() -> None:
    base = parameters(ev_charge_efficiency=1.0)
    true = parameters(ev_charge_efficiency=0.8)
    samples = (
        sample_from(true, sample_id="a", control=TwinControl(ev_charge_kw=4.0)),
        sample_from(true, sample_id="b", control=TwinControl(ev_charge_kw=8.0)),
    )
    report = calibrate_one(base, true, CalibratableParameter.EV_CHARGE_EFFICIENCY, 0.6, 1.0, samples=samples, weight_name="ev_soc")
    assert report.calibrated_parameters.ev_charge_efficiency == pytest.approx(0.8)


def test_multiple_parameters_are_calibrated_deterministically() -> None:
    base = parameters(thermal_capacity_kwh_per_c=10.0, heat_loss_kw_per_c=0.2)
    true = parameters(thermal_capacity_kwh_per_c=20.0, heat_loss_kw_per_c=0.4)
    samples = tuple(
        sample_from(
            true,
            sample_id=f"s-{index}",
            initial=state(indoor_temp_c=18.0 + index),
            control=TwinControl(hvac_thermal_kw=float(index % 3) * 2.0),
            weather=disturbance(outdoor_temp_c=4.0 + index),
        )
        for index in range(6)
    )
    calibrator = DigitalTwinCalibrator(
        CalibrationPolicy(
            rounds=4,
            minimum_absolute_improvement=0.0,
            minimum_relative_improvement=0.0,
            weights=only_weight("indoor_temp_c"),
        )
    )
    bounds = (
        ParameterBounds(CalibratableParameter.THERMAL_CAPACITY_KWH_PER_C, 5.0, 25.0, 5),
        ParameterBounds(CalibratableParameter.HEAT_LOSS_KW_PER_C, 0.1, 0.5, 5),
    )
    first = calibrator.calibrate(base, samples, bounds, generated_at=NOW)
    second = calibrator.calibrate(base, samples, reversed(bounds), generated_at=NOW + HOUR)
    assert first.calibrated_parameters == second.calibrated_parameters
    assert first.report_id == second.report_id


def test_generated_at_does_not_change_report_id() -> None:
    samples = (sample_from(parameters()),)
    bounds = [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)]
    first = DigitalTwinCalibrator().calibrate(parameters(), samples, bounds, generated_at=NOW)
    second = DigitalTwinCalibrator().calibrate(parameters(), samples, bounds, generated_at=NOW + HOUR)
    assert first.report_id == second.report_id


def test_changed_sample_id_changes_report_id() -> None:
    bounds = [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)]
    first = DigitalTwinCalibrator().calibrate(parameters(), [sample_from(parameters(), sample_id="a")], bounds, generated_at=NOW)
    second = DigitalTwinCalibrator().calibrate(parameters(), [sample_from(parameters(), sample_id="b")], bounds, generated_at=NOW)
    assert first.report_id != second.report_id


def test_calibrated_version_is_derived() -> None:
    true = parameters(hvac_cop=2.0)
    report = calibrate_one(parameters(), true, CalibratableParameter.HVAC_COP, 2.0, 6.0, samples=(sample_from(true, control=TwinControl(hvac_thermal_kw=4.0)),), weight_name="grid_import_kwh")
    assert report.calibrated_parameters.version.startswith("base-1+cal-")


def test_report_uses_validation_for_acceptance() -> None:
    base = parameters(hvac_cop=4.0)
    train_true = parameters(hvac_cop=2.0)
    validation_true = parameters(hvac_cop=4.0)
    training = [sample_from(train_true, sample_id="train", control=TwinControl(hvac_thermal_kw=4.0))]
    validation = [sample_from(validation_true, sample_id="validation", control=TwinControl(hvac_thermal_kw=4.0))]
    report = DigitalTwinCalibrator(
        CalibrationPolicy(
            minimum_absolute_improvement=0.0,
            minimum_relative_improvement=0.0,
            weights=only_weight("grid_import_kwh"),
        )
    ).calibrate(
        base,
        training,
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0, 5)],
        generated_at=NOW,
        validation_samples=validation,
    )
    assert report.validation_before is not None
    assert report.validation_after is not None
    assert not report.accepted


def test_report_recommends_base_when_rejected() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    assert not report.accepted
    assert report.recommended_parameters == report.base_parameters


def test_report_recommends_calibrated_when_accepted() -> None:
    true = parameters(hvac_cop=2.0)
    report = calibrate_one(parameters(), true, CalibratableParameter.HVAC_COP, 2.0, 6.0, samples=(sample_from(true, control=TwinControl(hvac_thermal_kw=4.0)),), weight_name="grid_import_kwh")
    assert report.accepted
    assert report.recommended_parameters == report.calibrated_parameters


def test_estimate_change_properties() -> None:
    estimate = ParameterEstimate(CalibratableParameter.HVAC_COP, 4.0, 2.0, 2.0, 6.0)
    assert estimate.absolute_change == -2.0
    assert estimate.relative_change == -0.5
    assert estimate.at_lower_bound
    assert not estimate.at_upper_bound


def test_report_is_frozen() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    with pytest.raises(FrozenInstanceError):
        report.accepted = True  # type: ignore[misc]


def test_serialization_round_trip_without_validation() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    assert loads_report(dumps_report(report)) == report


def test_serialization_round_trip_with_validation() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters(), sample_id="train")],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
        validation_samples=[sample_from(parameters(), sample_id="validation")],
    )
    assert loads_report(dumps_report(report)) == report


def test_serialization_is_deterministic() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    assert dumps_report(report) == dumps_report(report)


def test_loads_rejects_non_object_json() -> None:
    with pytest.raises(ValueError, match="object"):
        loads_report("[]")


def test_in_memory_repository_appends_and_gets() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    repository = InMemoryCalibrationRepository()
    assert repository.append(report) == report
    assert repository.get(report.report_id) == report
    assert repository.all() == (report,)


def test_in_memory_repository_is_idempotent() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    repository = InMemoryCalibrationRepository()
    repository.append(report)
    repository.append(report)
    assert len(repository.all()) == 1


def test_in_memory_repository_rejects_conflict() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    repository = InMemoryCalibrationRepository()
    repository.append(report)
    with pytest.raises(CalibrationConflictError):
        repository.append(replace(report, explanation="Different content"))


def test_repository_get_missing_raises() -> None:
    with pytest.raises(CalibrationNotFoundError):
        InMemoryCalibrationRepository().get("missing")


def test_jsonl_repository_persists(tmp_path) -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    path = tmp_path / "calibration.jsonl"
    repository = JsonlCalibrationRepository(path)
    repository.append(report)
    reloaded = JsonlCalibrationRepository(path)
    assert reloaded.get(report.report_id) == report


def test_jsonl_repository_does_not_duplicate_idempotent_append(tmp_path) -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    path = tmp_path / "calibration.jsonl"
    repository = JsonlCalibrationRepository(path)
    repository.append(report)
    repository.append(report)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_jsonl_repository_rejects_invalid_line(tmp_path) -> None:
    path = tmp_path / "calibration.jsonl"
    path.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        JsonlCalibrationRepository(path)


def test_explanation_states_advisory_boundary() -> None:
    report = DigitalTwinCalibrator().calibrate(
        parameters(),
        [sample_from(parameters())],
        [ParameterBounds(CalibratableParameter.HVAC_COP, 2.0, 6.0)],
        generated_at=NOW,
    )
    assert "does not activate parameters" in report.explanation
    assert "does not" in report.explanation
