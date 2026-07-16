from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from heos.digital_twin import TwinControl, TwinDisturbance, TwinParameters, TwinState
from heos.strategy import (
    ComfortBand,
    StrategyCandidate,
    StrategyObjective,
    StrategyPolicy,
    StrategyRequest,
    TariffStep,
)

DEMO_TIME = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class DemoScenario:
    scenario_id: str
    parameters: TwinParameters
    request: StrategyRequest
    candidates: tuple[StrategyCandidate, ...]
    policy: StrategyPolicy


def sunny_surplus_scenario() -> DemoScenario:
    parameters = TwinParameters(
        thermal_capacity_kwh_per_c=10.0,
        heat_loss_kw_per_c=0.2,
        hvac_cop=4.0,
        battery_capacity_kwh=10.0,
        battery_max_charge_kw=5.0,
        battery_max_discharge_kw=5.0,
        battery_charge_efficiency=0.95,
        battery_discharge_efficiency=0.95,
        ev_capacity_kwh=20.0,
        ev_max_charge_kw=3.6,
        ev_charge_efficiency=0.92,
        grid_max_import_kw=17.25,
        grid_max_export_kw=10.0,
        indoor_min_c=5.0,
        indoor_max_c=35.0,
        version="house-parameters-m22",
    )
    request = StrategyRequest(
        initial_state=TwinState(
            observed_at=DEMO_TIME,
            indoor_temp_c=21.0,
            battery_soc=0.55,
            ev_soc=0.35,
        ),
        disturbances=(
            TwinDisturbance(outdoor_temp_c=17.0, pv_kw=6.5, base_load_kw=1.2),
            TwinDisturbance(outdoor_temp_c=18.0, pv_kw=7.0, base_load_kw=1.1),
            TwinDisturbance(outdoor_temp_c=19.0, pv_kw=4.0, base_load_kw=1.2),
            TwinDisturbance(outdoor_temp_c=18.0, pv_kw=1.0, base_load_kw=1.3),
        ),
        tariffs=(
            TariffStep(0.20, 0.07),
            TariffStep(0.20, 0.07),
            TariffStep(0.28, 0.07),
            TariffStep(0.35, 0.07),
        ),
        comfort_bands=(ComfortBand(20.0, 22.0),),
        step_duration=timedelta(hours=1),
        generated_at=DEMO_TIME,
        metadata=(("site", "glass-box-demo"), ("weather", "sunny-surplus")),
    )
    candidates = (
        StrategyCandidate(
            candidate_id="solar-ev",
            name="Use solar surplus for EV charging",
            controls=(
                TwinControl(ev_charge_kw=3.6),
                TwinControl(ev_charge_kw=3.6),
                TwinControl(ev_charge_kw=2.0),
                TwinControl(),
            ),
            objective=StrategyObjective.EV_PRIORITY,
            tags=("ev", "solar", "self-consumption"),
        ),
        StrategyCandidate(
            candidate_id="battery-first",
            name="Prioritize battery reserve",
            controls=(
                TwinControl(battery_power_kw=4.0),
                TwinControl(battery_power_kw=4.0),
                TwinControl(battery_power_kw=-2.0),
                TwinControl(battery_power_kw=-2.0),
            ),
            objective=StrategyObjective.RESERVE,
            tags=("battery", "reserve"),
        ),
        StrategyCandidate(
            candidate_id="idle",
            name="Keep flexible loads idle",
            controls=(TwinControl(),) * 4,
            objective=StrategyObjective.BALANCED,
            tags=("baseline",),
        ),
    )
    policy = StrategyPolicy(
        energy_cost_weight=1.0,
        peak_import_weight=0.2,
        battery_throughput_weight=0.02,
        comfort_deviation_weight=4.0,
        ev_shortfall_weight=10.0,
        battery_reserve_shortfall_weight=5.0,
        violation_count_weight=1000.0,
        violation_magnitude_weight=100.0,
        target_ev_soc=0.70,
        reserve_battery_soc=0.30,
        require_feasible=True,
        version="strategy-policy-m22",
    )
    return DemoScenario(
        scenario_id="sunny-surplus-ev",
        parameters=parameters,
        request=request,
        candidates=candidates,
        policy=policy,
    )
