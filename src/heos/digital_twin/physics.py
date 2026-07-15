from __future__ import annotations

from dataclasses import dataclass

from .models import TwinParameters


@dataclass(frozen=True, slots=True)
class StorageFlow:
    requested_power_kw: float
    actual_power_kw: float
    next_soc: float
    limited: bool


@dataclass(frozen=True, slots=True)
class ThermalFlow:
    heat_loss_kw: float
    net_thermal_kw: float
    next_indoor_temp_c: float
    hvac_electric_kw: float


def battery_flow(
    *,
    requested_power_kw: float,
    soc: float,
    duration_hours: float,
    parameters: TwinParameters,
) -> StorageFlow:
    requested = float(requested_power_kw)
    if requested >= 0.0:
        capacity_limit = (
            parameters.battery_capacity_kwh
            * (1.0 - soc)
            / (parameters.battery_charge_efficiency * duration_hours)
        )
        actual = min(requested, parameters.battery_max_charge_kw, capacity_limit)
        delta = (
            actual
            * parameters.battery_charge_efficiency
            * duration_hours
            / parameters.battery_capacity_kwh
        )
    else:
        available_limit = (
            parameters.battery_capacity_kwh
            * soc
            * parameters.battery_discharge_efficiency
            / duration_hours
        )
        actual = -min(-requested, parameters.battery_max_discharge_kw, available_limit)
        delta = (
            actual
            / parameters.battery_discharge_efficiency
            * duration_hours
            / parameters.battery_capacity_kwh
        )
    next_soc = max(0.0, min(1.0, soc + delta))
    return StorageFlow(
        requested_power_kw=requested,
        actual_power_kw=actual,
        next_soc=next_soc,
        limited=abs(actual - requested) > 1e-12,
    )


def ev_flow(
    *,
    requested_power_kw: float,
    soc: float,
    duration_hours: float,
    parameters: TwinParameters,
) -> StorageFlow:
    requested = max(0.0, float(requested_power_kw))
    capacity_limit = (
        parameters.ev_capacity_kwh
        * (1.0 - soc)
        / (parameters.ev_charge_efficiency * duration_hours)
    )
    actual = min(requested, parameters.ev_max_charge_kw, capacity_limit)
    delta = (
        actual
        * parameters.ev_charge_efficiency
        * duration_hours
        / parameters.ev_capacity_kwh
    )
    return StorageFlow(
        requested_power_kw=requested,
        actual_power_kw=actual,
        next_soc=max(0.0, min(1.0, soc + delta)),
        limited=abs(actual - requested) > 1e-12,
    )


def thermal_flow(
    *,
    indoor_temp_c: float,
    outdoor_temp_c: float,
    hvac_thermal_kw: float,
    solar_gain_kw: float,
    internal_gain_kw: float,
    duration_hours: float,
    parameters: TwinParameters,
) -> ThermalFlow:
    heat_loss = parameters.heat_loss_kw_per_c * (indoor_temp_c - outdoor_temp_c)
    net_thermal = hvac_thermal_kw + solar_gain_kw + internal_gain_kw - heat_loss
    delta_temp = net_thermal * duration_hours / parameters.thermal_capacity_kwh_per_c
    hvac_electric = abs(hvac_thermal_kw) / parameters.hvac_cop
    return ThermalFlow(
        heat_loss_kw=heat_loss,
        net_thermal_kw=net_thermal,
        next_indoor_temp_c=indoor_temp_c + delta_temp,
        hvac_electric_kw=hvac_electric,
    )
