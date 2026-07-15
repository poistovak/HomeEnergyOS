from __future__ import annotations

from heos.digital_twin import TwinTrace

from .models import ComfortBand, StrategyMetrics, StrategyPolicy, TariffStep


def score_trace(
    trace: TwinTrace,
    tariffs: tuple[TariffStep, ...],
    comfort_bands: tuple[ComfortBand, ...],
    policy: StrategyPolicy,
) -> StrategyMetrics:
    if len(trace.steps) != len(tariffs):
        raise ValueError("tariffs must match trace steps")
    if len(trace.steps) != len(comfort_bands):
        raise ValueError("comfort_bands must match trace steps")

    total_import = 0.0
    total_export = 0.0
    net_cost = 0.0
    peak_import = 0.0
    comfort_deviation = 0.0
    violation_count = 0
    violation_magnitude = 0.0

    for step, tariff, band in zip(trace.steps, tariffs, comfort_bands, strict=True):
        imported = step.grid_import_kw * step.duration_hours
        exported = step.grid_export_kw * step.duration_hours
        total_import += imported
        total_export += exported
        net_cost += imported * tariff.import_price_per_kwh
        net_cost -= exported * tariff.export_price_per_kwh
        peak_import = max(peak_import, step.grid_import_kw)

        temperature = step.next_state.indoor_temp_c
        if temperature < band.minimum_c:
            comfort_deviation += (band.minimum_c - temperature) * step.duration_hours
        elif temperature > band.maximum_c:
            comfort_deviation += (temperature - band.maximum_c) * step.duration_hours

        violation_count += len(step.violations)
        violation_magnitude += sum(item.magnitude for item in step.violations)

    throughput = (
        trace.final_state.battery_throughput_kwh
        - trace.initial_state.battery_throughput_kwh
    )
    ev_shortfall = max(0.0, policy.target_ev_soc - trace.final_state.ev_soc)
    reserve_shortfall = max(0.0, policy.reserve_battery_soc - trace.final_state.battery_soc)

    score = (
        policy.energy_cost_weight * net_cost
        + policy.peak_import_weight * peak_import
        + policy.battery_throughput_weight * throughput
        + policy.comfort_deviation_weight * comfort_deviation
        + policy.ev_shortfall_weight * ev_shortfall
        + policy.battery_reserve_shortfall_weight * reserve_shortfall
        + policy.violation_count_weight * violation_count
        + policy.violation_magnitude_weight * violation_magnitude
    )

    return StrategyMetrics(
        total_grid_import_kwh=total_import,
        total_grid_export_kwh=total_export,
        net_energy_cost=net_cost,
        peak_grid_import_kw=peak_import,
        battery_throughput_kwh=throughput,
        comfort_deviation_degree_hours=comfort_deviation,
        ev_shortfall=ev_shortfall,
        battery_reserve_shortfall=reserve_shortfall,
        violation_count=violation_count,
        violation_magnitude=violation_magnitude,
        objective_score=score,
    )
