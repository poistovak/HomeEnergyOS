from datetime import UTC, datetime, timedelta

from heos.twin import DigitalTwin, TwinControl, TwinDisturbance, TwinParameters, TwinState

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
    version="liptov-house-1",
)

twin = DigitalTwin(parameters)
initial = TwinState(
    observed_at=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
    indoor_temp_c=22.0,
    battery_soc=0.45,
    ev_soc=0.30,
)

trace = twin.simulate(
    initial,
    controls=(
        TwinControl(battery_power_kw=2.0, ev_charge_kw=3.6),
        TwinControl(battery_power_kw=1.0, ev_charge_kw=3.6),
    ),
    disturbances=(
        TwinDisturbance(outdoor_temp_c=24.0, pv_kw=8.0, base_load_kw=1.2),
        TwinDisturbance(outdoor_temp_c=25.0, pv_kw=6.0, base_load_kw=1.4),
    ),
    step_duration=timedelta(minutes=15),
    generated_at=datetime.now(UTC),
    metadata=(("scenario", "summer-pv-charge"),),
)

print(trace.trace_id)
print(trace.final_state)
print("feasible:", trace.feasible)
