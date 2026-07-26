from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from heos.digital_twin import TwinControl, TwinDisturbance, TwinParameters, TwinState
from heos.strategy import (
    ComfortBand,
    NoFeasibleStrategyError,
    StandardStrategyFactory,
    StrategyCandidate,
    StrategyEngine,
    StrategyObjective,
    StrategyPolicy,
    StrategyRequest,
    TariffStep,
    decision_from_dict,
    decision_to_dict,
    dumps_decision,
    loads_decision,
    parameters_from_calibration,
)

NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)
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
        "version": "house-strategy-a",
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
        "outdoor_temp_c": 20.0,
        "pv_kw": 0.0,
        "base_load_kw": 1.0,
        "solar_gain_kw": 0.0,
        "internal_gain_kw": 0.0,
    }
    values.update(overrides)
    return TwinDisturbance(**values)


def request(
    *,
    disturbances: tuple[TwinDisturbance, ...] | None = None,
    tariffs: tuple[TariffStep, ...] | None = None,
    bands: tuple[ComfortBand, ...] | None = None,
    initial_state: TwinState | None = None,
    generated_at: datetime = NOW,
    metadata: tuple[tuple[str, str], ...] = (),
) -> StrategyRequest:
    active_disturbances = (disturbance(),) if disturbances is None else disturbances
    return StrategyRequest(
        initial_state=initial_state or state(),
        disturbances=active_disturbances,
        tariffs=tariffs or (TariffStep(0.2, 0.05),),
        comfort_bands=bands or (ComfortBand(19.0, 22.0),),
        step_duration=HOUR,
        generated_at=generated_at,
        metadata=metadata,
    )


def candidate(
    candidate_id: str = "candidate-a",
    *,
    controls: tuple[TwinControl, ...] | None = None,
    objective: StrategyObjective = StrategyObjective.BALANCED,
    tags: tuple[str, ...] = (),
) -> StrategyCandidate:
    return StrategyCandidate(
        candidate_id=candidate_id,
        name=candidate_id,
        controls=(TwinControl(),) if controls is None else controls,
        objective=objective,
        tags=tags,
    )


def energy_only_policy(**overrides: object) -> StrategyPolicy:
    values: dict[str, object] = {
        "energy_cost_weight": 1.0,
        "peak_import_weight": 0.0,
        "battery_throughput_weight": 0.0,
        "comfort_deviation_weight": 0.0,
        "ev_shortfall_weight": 0.0,
        "battery_reserve_shortfall_weight": 0.0,
        "violation_count_weight": 0.0,
        "violation_magnitude_weight": 0.0,
    }
    values.update(overrides)
    return StrategyPolicy(**values)  # type: ignore[arg-type]


def selected_decision():
    engine = StrategyEngine(parameters(), policy=energy_only_policy())
    return engine.select(
        (
            candidate("idle"),
            candidate("discharge", controls=(TwinControl(battery_power_kw=-1.0),)),
        ),
        request(),
    )


@pytest.mark.parametrize("value", [-1.0, float("inf"), float("nan")])
def test_tariff_rejects_invalid_import_price(value: float) -> None:
    with pytest.raises(ValueError, match="import_price"):
        TariffStep(value)


def test_tariff_rejects_negative_export_price() -> None:
    with pytest.raises(ValueError, match="export_price"):
        TariffStep(0.2, -0.1)


def test_comfort_band_rejects_reversed_bounds() -> None:
    with pytest.raises(ValueError, match="maximum_c"):
        ComfortBand(22.0, 20.0)


def test_comfort_band_midpoint() -> None:
    assert ComfortBand(18.0, 22.0).midpoint_c == 20.0


def test_candidate_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(" ")


def test_candidate_rejects_empty_controls() -> None:
    with pytest.raises(ValueError, match="controls"):
        candidate(controls=())


def test_candidate_normalizes_tags() -> None:
    item = candidate(tags=("z", "a", "z"))
    assert item.tags == ("a", "z")


def test_request_rejects_empty_disturbances() -> None:
    with pytest.raises(ValueError, match="disturbances"):
        request(disturbances=())


def test_request_rejects_tariff_length_mismatch() -> None:
    with pytest.raises(ValueError, match="tariffs"):
        request(
            disturbances=(disturbance(), disturbance()),
            tariffs=(TariffStep(0.1), TariffStep(0.2), TariffStep(0.3)),
        )


def test_request_rejects_band_length_mismatch() -> None:
    with pytest.raises(ValueError, match="comfort_bands"):
        request(
            disturbances=(disturbance(), disturbance()),
            bands=(ComfortBand(18.0, 22.0),) * 3,
        )


def test_request_rejects_zero_duration() -> None:
    with pytest.raises(ValueError, match="step_duration"):
        StrategyRequest(
            state(),
            (disturbance(),),
            (TariffStep(0.2),),
            (ComfortBand(18.0, 22.0),),
            timedelta(0),
            NOW,
        )


def test_request_rejects_naive_generated_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        # tests/test_strategy_engine.py
         request(
             generated_at=datetime(2026, 7, 15, 18, 0),  # noqa: DTZ001
)


def test_request_expands_single_tariff() -> None:
    item = request(disturbances=(disturbance(), disturbance()))
    assert len(item.expanded_tariffs) == 2


def test_request_expands_single_comfort_band() -> None:
    item = request(disturbances=(disturbance(), disturbance()))
    assert len(item.expanded_comfort_bands) == 2


def test_request_sorts_metadata() -> None:
    item = request(metadata=(("z", "2"), ("a", "1")))
    assert item.metadata == (("a", "1"), ("z", "2"))


@pytest.mark.parametrize(
    "field",
    [
        "energy_cost_weight",
        "peak_import_weight",
        "battery_throughput_weight",
        "comfort_deviation_weight",
        "ev_shortfall_weight",
        "battery_reserve_shortfall_weight",
        "violation_count_weight",
        "violation_magnitude_weight",
    ],
)
def test_policy_rejects_negative_weight(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        StrategyPolicy(**{field: -1.0})


def test_policy_rejects_all_zero_weights() -> None:
    with pytest.raises(ValueError, match="at least one"):
        energy_only_policy(energy_cost_weight=0.0)


def test_policy_rejects_invalid_target_soc() -> None:
    with pytest.raises(ValueError, match="target_ev_soc"):
        StrategyPolicy(target_ev_soc=1.1)


def test_engine_evaluate_builds_trace() -> None:
    evaluation = StrategyEngine(parameters()).evaluate(candidate(), request())
    assert len(evaluation.trace.steps) == 1
    assert evaluation.trace.metadata[0][0] in {"strategy_candidate_id", "strategy_objective"}


def test_engine_rejects_candidate_horizon_mismatch() -> None:
    with pytest.raises(ValueError, match="horizon"):
        StrategyEngine(parameters()).evaluate(
            candidate(controls=(TwinControl(), TwinControl())),
            request(),
        )


def test_metrics_calculate_grid_import() -> None:
    evaluation = StrategyEngine(parameters(), policy=energy_only_policy()).evaluate(
        candidate(),
        request(disturbances=(disturbance(base_load_kw=2.0),)),
    )
    assert evaluation.metrics.total_grid_import_kwh == pytest.approx(2.0)
    assert evaluation.metrics.net_energy_cost == pytest.approx(0.4)


def test_metrics_calculate_export_revenue() -> None:
    evaluation = StrategyEngine(parameters(), policy=energy_only_policy()).evaluate(
        candidate(),
        request(disturbances=(disturbance(base_load_kw=0.0, pv_kw=2.0),)),
    )
    assert evaluation.metrics.total_grid_export_kwh == pytest.approx(2.0)
    assert evaluation.metrics.net_energy_cost == pytest.approx(-0.1)


def test_metrics_calculate_peak_import() -> None:
    req = request(
        disturbances=(disturbance(base_load_kw=1.0), disturbance(base_load_kw=3.0)),
        tariffs=(TariffStep(0.2),),
    )
    evaluation = StrategyEngine(parameters()).evaluate(
        candidate(controls=(TwinControl(), TwinControl())),
        req,
    )
    assert evaluation.metrics.peak_grid_import_kw == pytest.approx(3.0)


def test_metrics_calculate_battery_throughput() -> None:
    evaluation = StrategyEngine(parameters()).evaluate(
        candidate(controls=(TwinControl(battery_power_kw=2.0),)),
        request(disturbances=(disturbance(base_load_kw=0.0),)),
    )
    assert evaluation.metrics.battery_throughput_kwh == pytest.approx(2.0)


def test_metrics_calculate_low_comfort_deviation() -> None:
    evaluation = StrategyEngine(parameters()).evaluate(
        candidate(),
        request(
            disturbances=(disturbance(outdoor_temp_c=0.0, base_load_kw=0.0),),
            bands=(ComfortBand(20.0, 22.0),),
        ),
    )
    assert evaluation.metrics.comfort_deviation_degree_hours > 0.0


def test_metrics_calculate_high_comfort_deviation() -> None:
    evaluation = StrategyEngine(parameters()).evaluate(
        candidate(controls=(TwinControl(hvac_thermal_kw=30.0),)),
        request(
            disturbances=(disturbance(outdoor_temp_c=20.0, base_load_kw=0.0),),
            bands=(ComfortBand(18.0, 21.0),),
        ),
    )
    assert evaluation.metrics.comfort_deviation_degree_hours > 0.0


def test_metrics_calculate_ev_shortfall() -> None:
    policy = energy_only_policy(energy_cost_weight=1.0, target_ev_soc=0.8)
    evaluation = StrategyEngine(parameters(), policy=policy).evaluate(candidate(), request())
    assert evaluation.metrics.ev_shortfall == pytest.approx(0.55)


def test_metrics_calculate_battery_reserve_shortfall() -> None:
    policy = energy_only_policy(energy_cost_weight=1.0, reserve_battery_soc=0.8)
    evaluation = StrategyEngine(parameters(), policy=policy).evaluate(candidate(), request())
    assert evaluation.metrics.battery_reserve_shortfall == pytest.approx(0.3)


def test_metrics_count_violations() -> None:
    evaluation = StrategyEngine(parameters(grid_max_import_kw=0.5)).evaluate(
        candidate(),
        request(),
    )
    assert evaluation.metrics.violation_count == 1
    assert evaluation.metrics.violation_magnitude == pytest.approx(0.5)
    assert not evaluation.feasible


def test_energy_only_score_equals_net_cost() -> None:
    evaluation = StrategyEngine(parameters(), policy=energy_only_policy()).evaluate(
        candidate(),
        request(),
    )
    assert evaluation.metrics.objective_score == evaluation.metrics.net_energy_cost


def test_select_prefers_lower_cost() -> None:
    decision = selected_decision()
    assert decision.selected.candidate.candidate_id == "discharge"


def test_select_orders_contiguous_ranks() -> None:
    decision = selected_decision()
    assert [item.rank for item in decision.alternatives] == [1, 2]


def test_select_rejects_empty_candidates() -> None:
    with pytest.raises(ValueError, match="candidates"):
        StrategyEngine(parameters()).select((), request())


def test_select_rejects_duplicate_candidate_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        StrategyEngine(parameters()).select((candidate("x"), candidate("x")), request())


def test_strict_policy_prefers_feasible_candidate() -> None:
    policy = energy_only_policy(require_feasible=True)
    decision = StrategyEngine(parameters(battery_max_discharge_kw=1.0), policy=policy).select(
        (
            candidate("feasible"),
            candidate("limited", controls=(TwinControl(battery_power_kw=-10.0),)),
        ),
        request(),
    )
    assert decision.selected.candidate.candidate_id == "feasible"


def test_strict_policy_raises_when_none_feasible() -> None:
    engine = StrategyEngine(parameters(grid_max_import_kw=0.0))
    with pytest.raises(NoFeasibleStrategyError):
        engine.select((candidate("a"), candidate("b")), request())


def test_non_strict_policy_can_select_infeasible_candidate() -> None:
    policy = energy_only_policy(require_feasible=False)
    decision = StrategyEngine(
        parameters(grid_max_import_kw=0.0, battery_max_discharge_kw=5.0),
        policy=policy,
    ).select(
        (
            candidate("idle"),
            candidate("discharge", controls=(TwinControl(battery_power_kw=-1.0),)),
        ),
        request(),
    )
    assert decision.selected.candidate.candidate_id == "discharge"


def test_tie_breaks_by_objective() -> None:
    decision = StrategyEngine(parameters(), policy=energy_only_policy()).select(
        (
            candidate("comfort", objective=StrategyObjective.COMFORT),
            candidate("cost", objective=StrategyObjective.COST),
        ),
        request(),
    )
    assert decision.selected.candidate.candidate_id == "comfort"


def test_tie_breaks_by_candidate_id() -> None:
    decision = StrategyEngine(parameters(), policy=energy_only_policy()).select(
        (candidate("z"), candidate("a")),
        request(),
    )
    assert decision.selected.candidate.candidate_id == "a"


def test_decision_id_is_deterministic() -> None:
    first = selected_decision()
    second = selected_decision()
    assert first.decision_id == second.decision_id


def test_decision_id_is_independent_of_input_order() -> None:
    engine = StrategyEngine(parameters(), policy=energy_only_policy())
    a = candidate("idle")
    b = candidate("discharge", controls=(TwinControl(battery_power_kw=-1.0),))
    assert engine.select((a, b), request()).decision_id == engine.select((b, a), request()).decision_id


def test_decision_id_changes_with_generated_at() -> None:
    engine = StrategyEngine(parameters(), policy=energy_only_policy())
    candidates = (candidate("a"), candidate("b"))
    first = engine.select(candidates, request(generated_at=NOW))
    second = engine.select(candidates, request(generated_at=NOW + timedelta(minutes=1)))
    assert first.decision_id != second.decision_id


def test_decision_explains_advisory_boundary() -> None:
    assert "advisory" in selected_decision().explanation.lower()


def test_evaluation_explains_advisory_boundary() -> None:
    evaluation = StrategyEngine(parameters()).evaluate(candidate(), request())
    assert "does not command devices" in evaluation.explanation


def test_factory_builds_six_standard_candidates() -> None:
    items = StandardStrategyFactory(parameters()).build(request())
    assert len(items) == 6


def test_factory_candidate_ids_are_unique() -> None:
    items = StandardStrategyFactory(parameters()).build(request())
    assert len({item.candidate_id for item in items}) == len(items)


def test_factory_controls_match_horizon() -> None:
    req = request(disturbances=(disturbance(), disturbance()))
    items = StandardStrategyFactory(parameters()).build(req)
    assert all(len(item.controls) == 2 for item in items)


def test_factory_self_consumption_charges_on_surplus() -> None:
    req = request(disturbances=(disturbance(base_load_kw=1.0, pv_kw=4.0),))
    items = StandardStrategyFactory(parameters()).build(req)
    item = next(value for value in items if value.candidate_id == "standard:self-consumption")
    assert item.controls[0].battery_power_kw == 3.0


def test_factory_self_consumption_discharges_on_deficit() -> None:
    req = request(disturbances=(disturbance(base_load_kw=4.0, pv_kw=1.0),))
    items = StandardStrategyFactory(parameters()).build(req)
    item = next(value for value in items if value.candidate_id == "standard:self-consumption")
    assert item.controls[0].battery_power_kw == -3.0


def test_factory_comfort_requests_heat_in_cold_weather() -> None:
    req = request(disturbances=(disturbance(outdoor_temp_c=0.0),))
    items = StandardStrategyFactory(parameters()).build(req)
    item = next(value for value in items if value.candidate_id == "standard:comfort")
    assert item.controls[0].hvac_thermal_kw > 0.0


def test_factory_reserve_charges_below_target() -> None:
    policy = StrategyPolicy(reserve_battery_soc=0.8)
    req = request(initial_state=state(battery_soc=0.2))
    items = StandardStrategyFactory(parameters(), policy=policy).build(req)
    item = next(value for value in items if value.candidate_id == "standard:reserve")
    assert item.controls[0].battery_power_kw == 5.0


def test_factory_reserve_is_idle_above_target() -> None:
    policy = StrategyPolicy(reserve_battery_soc=0.3)
    items = StandardStrategyFactory(parameters(), policy=policy).build(request())
    item = next(value for value in items if value.candidate_id == "standard:reserve")
    assert item.controls[0].battery_power_kw == 0.0


def test_factory_ev_priority_uses_max_power() -> None:
    items = StandardStrategyFactory(parameters(ev_max_charge_kw=3.6)).build(request())
    item = next(value for value in items if value.candidate_id == "standard:ev-priority")
    assert item.controls[0].ev_charge_kw == 3.6


def test_decision_serialization_round_trip() -> None:
    decision = selected_decision()
    assert loads_decision(dumps_decision(decision)) == decision


def test_decision_dict_round_trip() -> None:
    decision = selected_decision()
    assert decision_from_dict(decision_to_dict(decision)) == decision


def test_decision_from_dict_rejects_missing_selected_candidate() -> None:
    data = decision_to_dict(selected_decision())
    data["selected_candidate_id"] = "missing"
    with pytest.raises(ValueError, match="not present"):
        decision_from_dict(data)


def test_loads_decision_rejects_non_object() -> None:
    with pytest.raises(TypeError, match="object"):
        loads_decision("[]")


def test_parameters_from_calibration_uses_recommended_parameters() -> None:
    class Report:
        recommended_parameters = parameters(version="calibrated")

    assert parameters_from_calibration(Report()).version == "calibrated"


def test_parameters_from_calibration_rejects_wrong_type() -> None:
    class Report:
        recommended_parameters = object()

    with pytest.raises(TypeError, match="TwinParameters"):
        parameters_from_calibration(Report())


def test_candidate_is_frozen() -> None:
    item = candidate()
    with pytest.raises(FrozenInstanceError):
        item.name = "changed"  # type: ignore[misc]


def test_policy_is_frozen() -> None:
    item = StrategyPolicy()
    with pytest.raises(FrozenInstanceError):
        item.version = "changed"  # type: ignore[misc]

