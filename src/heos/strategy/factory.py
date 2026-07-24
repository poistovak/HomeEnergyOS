from __future__ import annotations

from heos.digital_twin import TwinControl, TwinParameters

from .models import StrategyCandidate, StrategyObjective, StrategyPolicy, StrategyRequest


class StandardStrategyFactory:
    def __init__(
        self,
        parameters: TwinParameters,
        *,
        policy: StrategyPolicy | None = None,
    ) -> None:
        self._parameters = parameters
        self._policy = policy or StrategyPolicy()

    def build(self, request: StrategyRequest) -> tuple[StrategyCandidate, ...]:
        idle = tuple(TwinControl() for _ in request.disturbances)
        comfort = tuple(
            TwinControl(hvac_thermal_kw=self._comfort_power(disturbance, band.midpoint_c))
            for disturbance, band in zip(
                request.disturbances,
                request.expanded_comfort_bands,
                strict=True,
            )
        )
        self_consumption = tuple(
            TwinControl(battery_power_kw=self._self_consumption_power(disturbance))
            for disturbance in request.disturbances
        )
        ev_priority = tuple(
            TwinControl(ev_charge_kw=self._parameters.ev_max_charge_kw)
            for _ in request.disturbances
        )
        reserve = tuple(
            TwinControl(battery_power_kw=self._reserve_power(request))
            for _ in request.disturbances
        )
        balanced = tuple(
            TwinControl(
                hvac_thermal_kw=comfort_step.hvac_thermal_kw,
                battery_power_kw=self_step.battery_power_kw,
                ev_charge_kw=self._parameters.ev_max_charge_kw * 0.5,
            )
            for comfort_step, self_step in zip(comfort, self_consumption, strict=True)
        )
        return (
            StrategyCandidate(
                "standard:balanced",
                "Balanced",
                balanced,
                StrategyObjective.BALANCED,
                ("standard",),
            ),
            StrategyCandidate(
                "standard:self-consumption",
                "Self-consumption",
                self_consumption,
                StrategyObjective.SELF_CONSUMPTION,
                ("standard",),
            ),
            StrategyCandidate(
                "standard:comfort",
                "Comfort first",
                comfort,
                StrategyObjective.COMFORT,
                ("standard",),
            ),
            StrategyCandidate(
                "standard:reserve",
                "Battery reserve",
                reserve,
                StrategyObjective.RESERVE,
                ("standard",),
            ),
            StrategyCandidate(
                "standard:ev-priority",
                "EV priority",
                ev_priority,
                StrategyObjective.EV_PRIORITY,
                ("standard",),
            ),
            StrategyCandidate(
                "standard:idle",
                "Idle baseline",
                idle,
                StrategyObjective.COST,
                ("baseline", "standard"),
            ),
        )

    def _comfort_power(self, disturbance: object, target_c: float) -> float:
        outdoor = float(disturbance.outdoor_temp_c)
        solar = float(disturbance.solar_gain_kw)
        internal = float(disturbance.internal_gain_kw)
        heat_loss = self._parameters.heat_loss_kw_per_c * (target_c - outdoor)
        return max(0.0, heat_loss - solar - internal)

    def _self_consumption_power(self, disturbance: object) -> float:
        pv = float(disturbance.pv_kw)
        load = float(disturbance.base_load_kw)
        surplus = pv - load
        if surplus >= 0.0:
            return min(surplus, self._parameters.battery_max_charge_kw)
        return -min(-surplus, self._parameters.battery_max_discharge_kw)

    def _reserve_power(self, request: StrategyRequest) -> float:
        if request.initial_state.battery_soc >= self._policy.reserve_battery_soc:
            return 0.0
        return self._parameters.battery_max_charge_kw
