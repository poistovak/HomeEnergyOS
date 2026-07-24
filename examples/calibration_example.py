from datetime import UTC, datetime, timedelta

from heos.calibration import (
    CalibratableParameter,
    CalibrationMetricWeights,
    CalibrationPolicy,
    CalibrationSample,
    DigitalTwinCalibrator,
    ParameterBounds,
)
from heos.digital_twin import DigitalTwin, TwinControl, TwinDisturbance, TwinParameters, TwinState

now = datetime.now(UTC)
base = TwinParameters(
    thermal_capacity_kwh_per_c=10.0,
    heat_loss_kw_per_c=0.2,
    hvac_cop=4.0,
    battery_capacity_kwh=10.0,
    battery_max_charge_kw=5.0,
    battery_max_discharge_kw=5.0,
)
initial = TwinState(observed_at=now, indoor_temp_c=21.0, battery_soc=0.5)
control = TwinControl(hvac_thermal_kw=4.0)
weather = TwinDisturbance(outdoor_temp_c=5.0, pv_kw=0.0, base_load_kw=1.0)

# In production this state comes from measured sensors, not from another simulation.
observed = DigitalTwin(
    TwinParameters(
        thermal_capacity_kwh_per_c=16.0,
        heat_loss_kw_per_c=0.2,
        hvac_cop=4.0,
        battery_capacity_kwh=10.0,
        battery_max_charge_kw=5.0,
        battery_max_discharge_kw=5.0,
    )
).step(initial, control, weather, duration=timedelta(hours=1)).next_state

sample = CalibrationSample(
    sample_id="example-hour-1",
    initial_state=initial,
    control=control,
    disturbance=weather,
    duration=timedelta(hours=1),
    observed_next_state=observed,
)
policy = CalibrationPolicy(
    weights=CalibrationMetricWeights(
        indoor_temp_c=1.0,
        battery_soc=0.0,
        ev_soc=0.0,
        grid_import_kwh=0.0,
        grid_export_kwh=0.0,
        battery_throughput_kwh=0.0,
    )
)
report = DigitalTwinCalibrator(policy).calibrate(
    base,
    [sample],
    [
        ParameterBounds(
            CalibratableParameter.THERMAL_CAPACITY_KWH_PER_C,
            minimum=8.0,
            maximum=20.0,
            candidates=7,
        )
    ],
    generated_at=now,
)

print(report.accepted)
print(report.calibrated_parameters.version)
print(report.estimates)
print(report.explanation)
