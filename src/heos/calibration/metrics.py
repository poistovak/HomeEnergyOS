from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from heos.digital_twin import DigitalTwin, TwinParameters

from .models import (
    CalibrationMetricScales,
    CalibrationMetrics,
    CalibrationMetricWeights,
    CalibrationSample,
)


@dataclass(frozen=True, slots=True)
class _Totals:
    indoor_temp: float = 0.0
    battery_soc: float = 0.0
    ev_soc: float = 0.0
    grid_import: float = 0.0
    grid_export: float = 0.0
    battery_throughput: float = 0.0
    weight: float = 0.0


def evaluate_parameters(
    parameters: TwinParameters,
    samples: Iterable[CalibrationSample],
    *,
    weights: CalibrationMetricWeights,
    scales: CalibrationMetricScales,
) -> CalibrationMetrics:
    normalized = tuple(samples)
    if not normalized:
        raise ValueError("samples must not be empty")

    twin = DigitalTwin(parameters)
    totals = _Totals()
    indoor = battery = ev = grid_import = grid_export = throughput = total_weight = 0.0

    for sample in normalized:
        result = twin.step(
            sample.initial_state,
            sample.control,
            sample.disturbance,
            duration=timedelta(hours=sample.duration_hours),
        )
        observed = sample.observed_next_state
        predicted = result.next_state
        factor = sample.weight

        indoor += abs(predicted.indoor_temp_c - observed.indoor_temp_c) * factor
        battery += abs(predicted.battery_soc - observed.battery_soc) * factor
        ev += abs(predicted.ev_soc - observed.ev_soc) * factor
        grid_import += abs(predicted.grid_import_kwh - observed.grid_import_kwh) * factor
        grid_export += abs(predicted.grid_export_kwh - observed.grid_export_kwh) * factor
        throughput += (
            abs(predicted.battery_throughput_kwh - observed.battery_throughput_kwh) * factor
        )
        total_weight += factor

    totals = _Totals(
        indoor_temp=indoor / total_weight,
        battery_soc=battery / total_weight,
        ev_soc=ev / total_weight,
        grid_import=grid_import / total_weight,
        grid_export=grid_export / total_weight,
        battery_throughput=throughput / total_weight,
        weight=total_weight,
    )

    weighted_terms = (
        weights.indoor_temp_c * totals.indoor_temp / scales.indoor_temp_c,
        weights.battery_soc * totals.battery_soc / scales.battery_soc,
        weights.ev_soc * totals.ev_soc / scales.ev_soc,
        weights.grid_import_kwh * totals.grid_import / scales.grid_import_kwh,
        weights.grid_export_kwh * totals.grid_export / scales.grid_export_kwh,
        weights.battery_throughput_kwh
        * totals.battery_throughput
        / scales.battery_throughput_kwh,
    )
    weight_sum = sum(
        (
            weights.indoor_temp_c,
            weights.battery_soc,
            weights.ev_soc,
            weights.grid_import_kwh,
            weights.grid_export_kwh,
            weights.battery_throughput_kwh,
        )
    )

    return CalibrationMetrics(
        indoor_temp_mae_c=totals.indoor_temp,
        battery_soc_mae=totals.battery_soc,
        ev_soc_mae=totals.ev_soc,
        grid_import_mae_kwh=totals.grid_import,
        grid_export_mae_kwh=totals.grid_export,
        battery_throughput_mae_kwh=totals.battery_throughput,
        weighted_loss=sum(weighted_terms) / weight_sum,
        sample_count=len(normalized),
        total_weight=totals.weight,
    )
