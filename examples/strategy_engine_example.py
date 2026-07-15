from datetime import UTC, datetime, timedelta

from heos.digital_twin import TwinDisturbance, TwinParameters, TwinState
from heos.strategy import (
    ComfortBand,
    StandardStrategyFactory,
    StrategyEngine,
    StrategyPolicy,
    StrategyRequest,
    TariffStep,
)

now = datetime.now(UTC)
parameters = TwinParameters(
    thermal_capacity_kwh_per_c=12.0,
    heat_loss_kw_per_c=0.22,
    hvac_cop=4.0,
    battery_capacity_kwh=10.0,
    battery_max_charge_kw=5.0,
    battery_max_discharge_kw=5.0,
    ev_capacity_kwh=34.0,
    ev_max_charge_kw=3.6,
    grid_max_import_kw=17.25,
    grid_max_export_kw=10.0,
    version="home-calibrated-1",
)
policy = StrategyPolicy(target_ev_soc=0.70, reserve_battery_soc=0.25)
request = StrategyRequest(
    initial_state=TwinState(now, indoor_temp_c=21.0, battery_soc=0.45, ev_soc=0.30),
    disturbances=(
        TwinDisturbance(8.0, pv_kw=1.0, base_load_kw=1.2),
        TwinDisturbance(9.0, pv_kw=4.0, base_load_kw=1.0),
        TwinDisturbance(10.0, pv_kw=6.0, base_load_kw=1.1),
    ),
    tariffs=(TariffStep(0.20, 0.06),),
    comfort_bands=(ComfortBand(20.0, 22.0),),
    step_duration=timedelta(hours=1),
    generated_at=now,
    metadata=(("source", "example"),),
)

factory = StandardStrategyFactory(parameters, policy=policy)
decision = StrategyEngine(parameters, policy=policy).select(factory.build(request), request)

print(decision.selected.candidate.name)
print(decision.selected.metrics.objective_score)
print(decision.explanation)
