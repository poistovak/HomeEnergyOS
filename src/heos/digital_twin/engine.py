from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from .correction import (
    CorrectionContext,
    NoResidualCorrection,
    ResidualCorrectionModel,
)
from .models import (
    ConstraintCode,
    ConstraintViolation,
    TwinControl,
    TwinDisturbance,
    TwinParameters,
    TwinState,
    TwinStepResult,
    TwinTrace,
    TwinVersion,
)
from .physics import battery_flow, ev_flow, thermal_flow


class InfeasibleTwinPlanError(RuntimeError):
    pass


class DigitalTwin:
    def __init__(
        self,
        parameters: TwinParameters,
        *,
        correction_model: ResidualCorrectionModel | None = None,
        version: TwinVersion | None = None,
    ) -> None:
        self._parameters = parameters
        self._correction_model = correction_model or NoResidualCorrection()
        active_version = version or TwinVersion()
        self._version = replace(
            active_version,
            parameter_version=parameters.version,
            correction_version=self._correction_model.version,
        )

    @property
    def parameters(self) -> TwinParameters:
        return self._parameters

    @property
    def version(self) -> TwinVersion:
        return self._version

    def step(
        self,
        state: TwinState,
        control: TwinControl,
        disturbance: TwinDisturbance,
        *,
        duration: timedelta,
        index: int = 0,
    ) -> TwinStepResult:
        duration_hours = duration.total_seconds() / 3600.0
        if duration_hours <= 0.0:
            raise ValueError("duration must be greater than zero")
        if index < 0:
            raise ValueError("index must be non-negative")

        correction = self._correction_model.predict(
            CorrectionContext(
                state=state,
                control=control,
                disturbance=disturbance,
                parameters=self._parameters,
                duration_hours=duration_hours,
            )
        )
        effective_load = max(0.0, disturbance.base_load_kw + correction.base_load_delta_kw)
        available_pv = max(0.0, disturbance.pv_kw + correction.pv_delta_kw)
        curtailed_pv = min(control.pv_curtailment_kw, available_pv)

        battery = battery_flow(
            requested_power_kw=control.battery_power_kw,
            soc=state.battery_soc,
            duration_hours=duration_hours,
            parameters=self._parameters,
        )
        ev = ev_flow(
            requested_power_kw=control.ev_charge_kw,
            soc=state.ev_soc,
            duration_hours=duration_hours,
            parameters=self._parameters,
        )
        thermal = thermal_flow(
            indoor_temp_c=state.indoor_temp_c,
            outdoor_temp_c=disturbance.outdoor_temp_c,
            hvac_thermal_kw=control.hvac_thermal_kw,
            solar_gain_kw=disturbance.solar_gain_kw,
            internal_gain_kw=disturbance.internal_gain_kw,
            duration_hours=duration_hours,
            parameters=self._parameters,
        )
        next_indoor_temp = thermal.next_indoor_temp_c + correction.indoor_temp_delta_c
        pv_to_bus = available_pv - curtailed_pv
        grid_power = (
            effective_load
            + thermal.hvac_electric_kw
            + ev.actual_power_kw
            + battery.actual_power_kw
            - pv_to_bus
        )
        ended_at = state.observed_at + duration
        next_state = TwinState(
            observed_at=ended_at,
            indoor_temp_c=next_indoor_temp,
            battery_soc=battery.next_soc,
            ev_soc=ev.next_soc,
            grid_import_kwh=(
                state.grid_import_kwh + max(0.0, grid_power) * duration_hours
            ),
            grid_export_kwh=(
                state.grid_export_kwh + max(0.0, -grid_power) * duration_hours
            ),
            battery_throughput_kwh=(
                state.battery_throughput_kwh
                + abs(battery.actual_power_kw) * duration_hours
            ),
        )
        violations = self._violations(
            control=control,
            available_pv=available_pv,
            battery_limited=battery.limited,
            actual_battery_power_kw=battery.actual_power_kw,
            ev_limited=ev.limited,
            actual_ev_power_kw=ev.actual_power_kw,
            grid_power_kw=grid_power,
            indoor_temp_c=next_indoor_temp,
        )
        return TwinStepResult(
            index=index,
            started_at=state.observed_at,
            ended_at=ended_at,
            duration_hours=duration_hours,
            prior_state=state,
            next_state=next_state,
            requested_control=control,
            disturbance=disturbance,
            correction=correction,
            actual_battery_power_kw=battery.actual_power_kw,
            actual_ev_charge_kw=ev.actual_power_kw,
            hvac_electric_kw=thermal.hvac_electric_kw,
            effective_base_load_kw=effective_load,
            available_pv_kw=available_pv,
            curtailed_pv_kw=curtailed_pv,
            grid_power_kw=grid_power,
            thermal_loss_kw=thermal.heat_loss_kw,
            net_thermal_kw=thermal.net_thermal_kw,
            violations=violations,
        )

    def simulate(
        self,
        initial_state: TwinState,
        controls: Iterable[TwinControl],
        disturbances: Iterable[TwinDisturbance],
        *,
        step_duration: timedelta,
        generated_at: datetime,
        metadata: Iterable[tuple[str, str]] = (),
        require_feasible: bool = False,
    ) -> TwinTrace:
        print("DEBUG generated_at =", generated_at, "tzinfo =", generated_at.tzinfo)
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        control_steps = tuple(controls)
        disturbance_steps = tuple(disturbances)
        if not control_steps:
            raise ValueError("controls must not be empty")
        if len(control_steps) != len(disturbance_steps):
            raise ValueError("controls and disturbances must have equal length")

        state = initial_state
        steps: list[TwinStepResult] = []
        for index, (control, disturbance) in enumerate(
            zip(control_steps, disturbance_steps, strict=True)
        ):
            result = self.step(
                state,
                control,
                disturbance,
                duration=step_duration,
                index=index,
            )
            steps.append(result)
            state = result.next_state

        trace_id = self._trace_id(initial_state, tuple(steps))
        trace = TwinTrace(
            trace_id=trace_id,
            generated_at=generated_at,
            parameters=self._parameters,
            version=self._version,
            initial_state=initial_state,
            steps=tuple(steps),
            final_state=state,
            explanation=(
                "Deterministic physics-first simulation with optional bounded residual correction."
            ),
            metadata=tuple(metadata),
        )
        if require_feasible and not trace.feasible:
            codes = sorted({violation.code.value for step in trace.steps for violation in step.violations})
            raise InfeasibleTwinPlanError("infeasible twin plan: " + ", ".join(codes))
        return trace

    def _violations(
        self,
        *,
        control: TwinControl,
        available_pv: float,
        battery_limited: bool,
        actual_battery_power_kw: float,
        ev_limited: bool,
        actual_ev_power_kw: float,
        grid_power_kw: float,
        indoor_temp_c: float,
    ) -> tuple[ConstraintViolation, ...]:
        violations: list[ConstraintViolation] = []
        if battery_limited:
            violations.append(
                ConstraintViolation(
                    code=ConstraintCode.BATTERY_POWER_LIMITED,
                    magnitude=abs(control.battery_power_kw - actual_battery_power_kw),
                    message="Requested battery power was clipped by power or state-of-charge limits.",
                )
            )
        if ev_limited:
            violations.append(
                ConstraintViolation(
                    code=ConstraintCode.EV_POWER_LIMITED,
                    magnitude=abs(control.ev_charge_kw - actual_ev_power_kw),
                    message="Requested EV charging power was clipped by charger or capacity limits.",
                )
            )
        if control.pv_curtailment_kw > available_pv:
            violations.append(
                ConstraintViolation(
                    code=ConstraintCode.PV_CURTAILMENT_LIMITED,
                    magnitude=control.pv_curtailment_kw - available_pv,
                    message="Requested PV curtailment exceeded available PV power.",
                )
            )
        if grid_power_kw > self._parameters.grid_max_import_kw:
            violations.append(
                ConstraintViolation(
                    code=ConstraintCode.GRID_IMPORT_LIMIT,
                    magnitude=grid_power_kw - self._parameters.grid_max_import_kw,
                    message="Predicted grid import exceeds the configured connection limit.",
                )
            )
        if -grid_power_kw > self._parameters.grid_max_export_kw:
            violations.append(
                ConstraintViolation(
                    code=ConstraintCode.GRID_EXPORT_LIMIT,
                    magnitude=-grid_power_kw - self._parameters.grid_max_export_kw,
                    message="Predicted grid export exceeds the configured connection limit.",
                )
            )
        if indoor_temp_c < self._parameters.indoor_min_c:
            violations.append(
                ConstraintViolation(
                    code=ConstraintCode.INDOOR_TEMPERATURE_LOW,
                    magnitude=self._parameters.indoor_min_c - indoor_temp_c,
                    message="Predicted indoor temperature is below the hard lower bound.",
                )
            )
        if indoor_temp_c > self._parameters.indoor_max_c:
            violations.append(
                ConstraintViolation(
                    code=ConstraintCode.INDOOR_TEMPERATURE_HIGH,
                    magnitude=indoor_temp_c - self._parameters.indoor_max_c,
                    message="Predicted indoor temperature is above the hard upper bound.",
                )
            )
        return tuple(violations)

    def _trace_id(self, initial_state: TwinState, steps: tuple[TwinStepResult, ...]) -> str:
        payload = {
            "version": {
                "schema": self._version.schema_version,
                "model": self._version.model_version,
                "parameters": self._version.parameter_version,
                "correction": self._version.correction_version,
            },
            "initial": {
                "at": initial_state.observed_at.isoformat(),
                "temp": initial_state.indoor_temp_c,
                "battery_soc": initial_state.battery_soc,
                "ev_soc": initial_state.ev_soc,
            },
            "steps": [
                {
                    "duration": step.duration_hours,
                    "control": {
                        "hvac": step.requested_control.hvac_thermal_kw,
                        "battery": step.requested_control.battery_power_kw,
                        "ev": step.requested_control.ev_charge_kw,
                        "curtail": step.requested_control.pv_curtailment_kw,
                    },
                    "disturbance": {
                        "outdoor": step.disturbance.outdoor_temp_c,
                        "pv": step.disturbance.pv_kw,
                        "load": step.disturbance.base_load_kw,
                        "solar": step.disturbance.solar_gain_kw,
                        "internal": step.disturbance.internal_gain_kw,
                    },
                    "correction": {
                        "temp": step.correction.indoor_temp_delta_c,
                        "load": step.correction.base_load_delta_kw,
                        "pv": step.correction.pv_delta_kw,
                        "source": step.correction.source,
                    },
                }
                for step in steps
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return str(uuid5(NAMESPACE_URL, f"heos-digital-twin:{digest}"))
