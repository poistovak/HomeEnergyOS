from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from heos.digital_twin import (
    ConstraintCode,
    ConstraintViolation,
    CorrectionVector,
    DigitalTwin,
    FixedResidualCorrection,
    HouseMemoryPatternCorrection,
    InfeasibleTwinPlanError,
    NoResidualCorrection,
    TwinControl,
    TwinDisturbance,
    TwinParameters,
    TwinState,
    TwinVersion,
    battery_flow,
    dumps_trace,
    ev_flow,
    loads_trace,
    thermal_flow,
)
from heos.feedback.models import OutcomeClassification
from heos.memory.models import PatternSummary

NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


def parameters(**overrides: float | str) -> TwinParameters:
    values: dict[str, float | str] = {
        "thermal_capacity_kwh_per_c": 10.0,
        "heat_loss_kw_per_c": 0.2,
        "hvac_cop": 4.0,
        "battery_capacity_kwh": 10.0,
        "battery_max_charge_kw": 5.0,
        "battery_max_discharge_kw": 5.0,
        "battery_charge_efficiency": 1.0,
        "battery_discharge_efficiency": 1.0,
        "ev_capacity_kwh": 20.0,
        "ev_max_charge_kw": 7.0,
        "ev_charge_efficiency": 1.0,
        "grid_max_import_kw": 100.0,
        "grid_max_export_kw": 100.0,
        "indoor_min_c": -50.0,
        "indoor_max_c": 50.0,
        "version": "house-a",
    }
    values.update(overrides)
    return TwinParameters(**values)  # type: ignore[arg-type]


def state(**overrides: float | datetime) -> TwinState:
    values: dict[str, float | datetime] = {
        "observed_at": NOW,
        "indoor_temp_c": 20.0,
        "battery_soc": 0.5,
        "ev_soc": 0.25,
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


def twin(**parameter_overrides: float | str) -> DigitalTwin:
    return DigitalTwin(parameters(**parameter_overrides))


def memory_pattern(
    targets: dict[str, float],
    *,
    quality: float = 0.5,
) -> PatternSummary:
    classification = OutcomeClassification.EXCELLENT
    return PatternSummary(
        pattern_id="pattern-1",
        generated_at=NOW,
        member_ids=("memory-1", "memory-2"),
        sample_count=2,
        feature_means={"outdoor_temp_c": 10.0},
        target_means=targets,
        mean_quality=quality,
        classification_counts={classification.value: 2},
        dominant_classification=classification,
    )


def test_version_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="model_version"):
        TwinVersion(model_version=" ")


def test_parameters_reject_zero_thermal_capacity() -> None:
    with pytest.raises(ValueError, match="thermal_capacity"):
        parameters(thermal_capacity_kwh_per_c=0.0)


def test_parameters_reject_zero_efficiency() -> None:
    with pytest.raises(ValueError, match="efficiency"):
        parameters(battery_charge_efficiency=0.0)


def test_parameters_reject_reversed_indoor_bounds() -> None:
    with pytest.raises(ValueError, match="indoor_max"):
        parameters(indoor_min_c=25.0, indoor_max_c=20.0)


def test_state_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        state(observed_at=datetime(2026, 7, 15, 12, 0))


def test_state_rejects_invalid_soc() -> None:
    with pytest.raises(ValueError, match="battery_soc"):
        state(battery_soc=1.1)


def test_control_rejects_negative_ev_power() -> None:
    with pytest.raises(ValueError, match="ev_charge_kw"):
        TwinControl(ev_charge_kw=-1.0)


def test_disturbance_rejects_negative_pv() -> None:
    with pytest.raises(ValueError, match="pv_kw"):
        disturbance(pv_kw=-1.0)


def test_correction_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="source"):
        CorrectionVector(source="")


def test_violation_rejects_negative_magnitude() -> None:
    with pytest.raises(ValueError, match="magnitude"):
        ConstraintViolation(ConstraintCode.GRID_IMPORT_LIMIT, -1.0, "bad")


def test_battery_charge_increases_soc() -> None:
    flow = battery_flow(
        requested_power_kw=2.0,
        soc=0.5,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.next_soc == pytest.approx(0.7)


def test_battery_discharge_decreases_soc() -> None:
    flow = battery_flow(
        requested_power_kw=-2.0,
        soc=0.5,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.next_soc == pytest.approx(0.3)


def test_battery_charge_respects_power_limit() -> None:
    flow = battery_flow(
        requested_power_kw=8.0,
        soc=0.2,
        duration_hours=1.0,
        parameters=parameters(battery_max_charge_kw=3.0),
    )
    assert flow.actual_power_kw == 3.0
    assert flow.limited


def test_battery_charge_respects_capacity_limit() -> None:
    flow = battery_flow(
        requested_power_kw=5.0,
        soc=0.9,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.actual_power_kw == pytest.approx(1.0)
    assert flow.next_soc == 1.0


def test_battery_discharge_respects_power_limit() -> None:
    flow = battery_flow(
        requested_power_kw=-8.0,
        soc=0.8,
        duration_hours=1.0,
        parameters=parameters(battery_max_discharge_kw=3.0),
    )
    assert flow.actual_power_kw == -3.0
    assert flow.limited


def test_battery_discharge_respects_capacity_limit() -> None:
    flow = battery_flow(
        requested_power_kw=-5.0,
        soc=0.1,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.actual_power_kw == pytest.approx(-1.0)
    assert flow.next_soc == 0.0


def test_ev_charge_increases_soc() -> None:
    flow = ev_flow(
        requested_power_kw=4.0,
        soc=0.25,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.next_soc == pytest.approx(0.45)


def test_ev_charge_respects_power_limit() -> None:
    flow = ev_flow(
        requested_power_kw=9.0,
        soc=0.25,
        duration_hours=1.0,
        parameters=parameters(ev_max_charge_kw=3.0),
    )
    assert flow.actual_power_kw == 3.0
    assert flow.limited


def test_thermal_equal_temperatures_have_no_loss() -> None:
    flow = thermal_flow(
        indoor_temp_c=20.0,
        outdoor_temp_c=20.0,
        hvac_thermal_kw=0.0,
        solar_gain_kw=0.0,
        internal_gain_kw=0.0,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.heat_loss_kw == 0.0
    assert flow.next_indoor_temp_c == 20.0


def test_thermal_loss_cools_house() -> None:
    flow = thermal_flow(
        indoor_temp_c=20.0,
        outdoor_temp_c=10.0,
        hvac_thermal_kw=0.0,
        solar_gain_kw=0.0,
        internal_gain_kw=0.0,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.next_indoor_temp_c == pytest.approx(19.8)


def test_thermal_heating_raises_temperature() -> None:
    flow = thermal_flow(
        indoor_temp_c=20.0,
        outdoor_temp_c=20.0,
        hvac_thermal_kw=5.0,
        solar_gain_kw=0.0,
        internal_gain_kw=0.0,
        duration_hours=1.0,
        parameters=parameters(),
    )
    assert flow.next_indoor_temp_c == pytest.approx(20.5)


def test_hvac_electric_power_uses_cop() -> None:
    flow = thermal_flow(
        indoor_temp_c=20.0,
        outdoor_temp_c=20.0,
        hvac_thermal_kw=8.0,
        solar_gain_kw=0.0,
        internal_gain_kw=0.0,
        duration_hours=1.0,
        parameters=parameters(hvac_cop=4.0),
    )
    assert flow.hvac_electric_kw == 2.0


def test_step_advances_time() -> None:
    result = twin().step(state(), TwinControl(), disturbance(), duration=HOUR)
    assert result.ended_at == NOW + HOUR
    assert result.next_state.observed_at == NOW + HOUR


def test_step_calculates_grid_import() -> None:
    result = twin().step(state(), TwinControl(), disturbance(base_load_kw=3.0), duration=HOUR)
    assert result.grid_import_kw == pytest.approx(3.0)


def test_step_calculates_grid_export() -> None:
    result = twin().step(
        state(),
        TwinControl(),
        disturbance(base_load_kw=1.0, pv_kw=4.0),
        duration=HOUR,
    )
    assert result.grid_export_kw == pytest.approx(3.0)


def test_step_accumulates_grid_import_energy() -> None:
    result = twin().step(state(grid_import_kwh=2.0), TwinControl(), disturbance(), duration=HOUR)
    assert result.next_state.grid_import_kwh == pytest.approx(3.0)


def test_step_accumulates_grid_export_energy() -> None:
    result = twin().step(
        state(grid_export_kwh=2.0),
        TwinControl(),
        disturbance(base_load_kw=0.0, pv_kw=2.0),
        duration=HOUR,
    )
    assert result.next_state.grid_export_kwh == pytest.approx(4.0)


def test_step_accumulates_battery_throughput() -> None:
    result = twin().step(
        state(battery_throughput_kwh=1.0),
        TwinControl(battery_power_kw=2.0),
        disturbance(base_load_kw=0.0),
        duration=HOUR,
    )
    assert result.next_state.battery_throughput_kwh == pytest.approx(3.0)


def test_pv_curtailment_reduces_export() -> None:
    result = twin().step(
        state(),
        TwinControl(pv_curtailment_kw=2.0),
        disturbance(base_load_kw=1.0, pv_kw=4.0),
        duration=HOUR,
    )
    assert result.grid_export_kw == pytest.approx(1.0)


def test_pv_curtailment_limit_is_reported() -> None:
    result = twin().step(
        state(),
        TwinControl(pv_curtailment_kw=5.0),
        disturbance(base_load_kw=0.0, pv_kw=2.0),
        duration=HOUR,
    )
    assert ConstraintCode.PV_CURTAILMENT_LIMITED in {item.code for item in result.violations}


def test_battery_limit_is_reported() -> None:
    result = twin(battery_max_charge_kw=1.0).step(
        state(),
        TwinControl(battery_power_kw=3.0),
        disturbance(base_load_kw=0.0),
        duration=HOUR,
    )
    assert ConstraintCode.BATTERY_POWER_LIMITED in {item.code for item in result.violations}


def test_ev_limit_is_reported() -> None:
    result = twin(ev_max_charge_kw=1.0).step(
        state(),
        TwinControl(ev_charge_kw=3.0),
        disturbance(base_load_kw=0.0),
        duration=HOUR,
    )
    assert ConstraintCode.EV_POWER_LIMITED in {item.code for item in result.violations}


def test_grid_import_limit_is_reported() -> None:
    result = twin(grid_max_import_kw=2.0).step(
        state(),
        TwinControl(),
        disturbance(base_load_kw=3.0),
        duration=HOUR,
    )
    assert ConstraintCode.GRID_IMPORT_LIMIT in {item.code for item in result.violations}


def test_grid_export_limit_is_reported() -> None:
    result = twin(grid_max_export_kw=2.0).step(
        state(),
        TwinControl(),
        disturbance(base_load_kw=0.0, pv_kw=3.0),
        duration=HOUR,
    )
    assert ConstraintCode.GRID_EXPORT_LIMIT in {item.code for item in result.violations}


def test_low_temperature_limit_is_reported() -> None:
    result = twin(indoor_min_c=19.9, indoor_max_c=40.0).step(
        state(),
        TwinControl(),
        disturbance(outdoor_temp_c=10.0, base_load_kw=0.0),
        duration=HOUR,
    )
    assert ConstraintCode.INDOOR_TEMPERATURE_LOW in {item.code for item in result.violations}


def test_high_temperature_limit_is_reported() -> None:
    result = twin(indoor_min_c=0.0, indoor_max_c=20.1).step(
        state(),
        TwinControl(hvac_thermal_kw=5.0),
        disturbance(outdoor_temp_c=20.0, base_load_kw=0.0),
        duration=HOUR,
    )
    assert ConstraintCode.INDOOR_TEMPERATURE_HIGH in {item.code for item in result.violations}


def test_feasible_step_property() -> None:
    result = twin().step(state(), TwinControl(), disturbance(), duration=HOUR)
    assert result.feasible


def test_infeasible_step_property() -> None:
    result = twin(grid_max_import_kw=0.5).step(
        state(), TwinControl(), disturbance(), duration=HOUR
    )
    assert not result.feasible


def test_fixed_correction_applies_load_delta() -> None:
    model = FixedResidualCorrection(CorrectionVector(base_load_delta_kw=2.0))
    result = DigitalTwin(parameters(), correction_model=model).step(
        state(), TwinControl(), disturbance(base_load_kw=1.0), duration=HOUR
    )
    assert result.effective_base_load_kw == 3.0


def test_fixed_correction_applies_pv_delta() -> None:
    model = FixedResidualCorrection(CorrectionVector(pv_delta_kw=2.0))
    result = DigitalTwin(parameters(), correction_model=model).step(
        state(), TwinControl(), disturbance(pv_kw=1.0), duration=HOUR
    )
    assert result.available_pv_kw == 3.0


def test_fixed_correction_applies_temperature_delta() -> None:
    model = FixedResidualCorrection(CorrectionVector(indoor_temp_delta_c=1.0))
    result = DigitalTwin(parameters(), correction_model=model).step(
        state(), TwinControl(), disturbance(outdoor_temp_c=20.0), duration=HOUR
    )
    assert result.next_state.indoor_temp_c == pytest.approx(21.0)


def test_no_correction_returns_zero_vector() -> None:
    model = NoResidualCorrection()
    result = DigitalTwin(parameters(), correction_model=model).step(
        state(), TwinControl(), disturbance(), duration=HOUR
    )
    assert result.correction == CorrectionVector()


def test_pattern_correction_is_quality_weighted() -> None:
    model = HouseMemoryPatternCorrection(
        memory_pattern({"base_load_error_kw": 2.0}, quality=0.5)
    )
    correction = model.predict(None)  # type: ignore[arg-type]
    assert correction.base_load_delta_kw == 1.0


def test_pattern_correction_can_disable_quality_weighting() -> None:
    model = HouseMemoryPatternCorrection(
        memory_pattern({"base_load_error_kw": 2.0}, quality=0.5),
        quality_weighted=False,
    )
    correction = model.predict(None)  # type: ignore[arg-type]
    assert correction.base_load_delta_kw == 2.0


def test_pattern_correction_clamps_temperature() -> None:
    model = HouseMemoryPatternCorrection(
        memory_pattern({"indoor_temp_error_c": 10.0}, quality=1.0),
        max_temp_delta_c=2.0,
    )
    assert model.predict(None).indoor_temp_delta_c == 2.0  # type: ignore[arg-type]


def test_pattern_correction_clamps_power() -> None:
    model = HouseMemoryPatternCorrection(
        memory_pattern({"pv_error_kw": -10.0}, quality=1.0),
        max_power_delta_kw=3.0,
    )
    assert model.predict(None).pv_delta_kw == -3.0  # type: ignore[arg-type]


def test_pattern_correction_missing_targets_are_zero() -> None:
    correction = HouseMemoryPatternCorrection(memory_pattern({})).predict(None)  # type: ignore[arg-type]
    assert correction.indoor_temp_delta_c == 0.0
    assert correction.base_load_delta_kw == 0.0
    assert correction.pv_delta_kw == 0.0


def test_simulate_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError, match="equal length"):
        twin().simulate(
            state(),
            [TwinControl()],
            [],
            step_duration=HOUR,
            generated_at=NOW,
        )


def test_simulate_rejects_empty_plan() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        twin().simulate(state(), [], [], step_duration=HOUR, generated_at=NOW)


def test_simulate_rejects_naive_generated_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        twin().simulate(
            state(),
            [TwinControl()],
            [disturbance()],
            step_duration=HOUR,
            generated_at=datetime(2026, 7, 15)  # noqa: DTZ001
        )


def test_simulate_builds_continuous_state_chain() -> None:
    trace = twin().simulate(
        state(),
        [TwinControl(), TwinControl()],
        [disturbance(), disturbance()],
        step_duration=HOUR,
        generated_at=NOW,
    )
    assert trace.steps[0].next_state == trace.steps[1].prior_state
    assert trace.final_state.observed_at == NOW + 2 * HOUR


def test_trace_id_is_deterministic() -> None:
    first = twin().simulate(
        state(),
        [TwinControl()],
        [disturbance()],
        step_duration=HOUR,
        generated_at=NOW,
    )
    second = twin().simulate(
        state(),
        [TwinControl()],
        [disturbance()],
        step_duration=HOUR,
        generated_at=NOW + timedelta(minutes=1),
    )
    assert first.trace_id == second.trace_id


def test_trace_id_changes_when_control_changes() -> None:
    first = twin().simulate(
        state(),
        [TwinControl()],
        [disturbance()],
        step_duration=HOUR,
        generated_at=NOW,
    )
    second = twin().simulate(
        state(),
        [TwinControl(battery_power_kw=1.0)],
        [disturbance()],
        step_duration=HOUR,
        generated_at=NOW,
    )
    assert first.trace_id != second.trace_id


def test_require_feasible_raises() -> None:
    with pytest.raises(InfeasibleTwinPlanError, match="grid_import_limit"):
        twin(grid_max_import_kw=0.5).simulate(
            state(),
            [TwinControl()],
            [disturbance()],
            step_duration=HOUR,
            generated_at=NOW,
            require_feasible=True,
        )


def test_trace_metadata_is_sorted() -> None:
    trace = twin().simulate(
        state(),
        [TwinControl()],
        [disturbance()],
        step_duration=HOUR,
        generated_at=NOW,
        metadata=(("z", "2"), ("a", "1")),
    )
    assert trace.metadata == (("a", "1"), ("z", "2"))


def test_trace_serialization_round_trip() -> None:
    trace = twin().simulate(
        state(),
        [TwinControl(battery_power_kw=1.0)],
        [disturbance(pv_kw=2.0)],
        step_duration=HOUR,
        generated_at=NOW,
        metadata=(("scenario", "sunny"),),
    )
    assert loads_trace(dumps_trace(trace)) == trace
         

def test_state_is_frozen() -> None:
    item = state()
    with pytest.raises(FrozenInstanceError):
        item.battery_soc = 0.1  # type: ignore[misc]
