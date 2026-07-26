from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .models import (
    ConstraintCode,
    ConstraintViolation,
    CorrectionVector,
    TwinControl,
    TwinDisturbance,
    TwinParameters,
    TwinState,
    TwinStepResult,
    TwinTrace,
    TwinVersion,
)


def _state_to_dict(state: TwinState) -> dict[str, Any]:
    return {
        "observed_at": state.observed_at.isoformat(),
        "indoor_temp_c": state.indoor_temp_c,
        "battery_soc": state.battery_soc,
        "ev_soc": state.ev_soc,
        "grid_import_kwh": state.grid_import_kwh,
        "grid_export_kwh": state.grid_export_kwh,
        "battery_throughput_kwh": state.battery_throughput_kwh,
    }


def _state_from_dict(data: Mapping[str, Any]) -> TwinState:
    return TwinState(
        observed_at=datetime.fromisoformat(str(data["observed_at"])),
        indoor_temp_c=float(data["indoor_temp_c"]),
        battery_soc=float(data["battery_soc"]),
        ev_soc=float(data["ev_soc"]),
        grid_import_kwh=float(data["grid_import_kwh"]),
        grid_export_kwh=float(data["grid_export_kwh"]),
        battery_throughput_kwh=float(data["battery_throughput_kwh"]),
    )


def _control_to_dict(control: TwinControl) -> dict[str, float]:
    return {
        "hvac_thermal_kw": control.hvac_thermal_kw,
        "battery_power_kw": control.battery_power_kw,
        "ev_charge_kw": control.ev_charge_kw,
        "pv_curtailment_kw": control.pv_curtailment_kw,
    }


def _control_from_dict(data: Mapping[str, Any]) -> TwinControl:
    return TwinControl(**{key: float(value) for key, value in data.items()})


def _disturbance_to_dict(disturbance: TwinDisturbance) -> dict[str, float]:
    return {
        "outdoor_temp_c": disturbance.outdoor_temp_c,
        "pv_kw": disturbance.pv_kw,
        "base_load_kw": disturbance.base_load_kw,
        "solar_gain_kw": disturbance.solar_gain_kw,
        "internal_gain_kw": disturbance.internal_gain_kw,
    }


def _disturbance_from_dict(data: Mapping[str, Any]) -> TwinDisturbance:
    return TwinDisturbance(**{key: float(value) for key, value in data.items()})


def _correction_to_dict(correction: CorrectionVector) -> dict[str, Any]:
    return {
        "indoor_temp_delta_c": correction.indoor_temp_delta_c,
        "base_load_delta_kw": correction.base_load_delta_kw,
        "pv_delta_kw": correction.pv_delta_kw,
        "source": correction.source,
        "explanation": correction.explanation,
    }


def _correction_from_dict(data: Mapping[str, Any]) -> CorrectionVector:
    return CorrectionVector(
        indoor_temp_delta_c=float(data["indoor_temp_delta_c"]),
        base_load_delta_kw=float(data["base_load_delta_kw"]),
        pv_delta_kw=float(data["pv_delta_kw"]),
        source=str(data["source"]),
        explanation=str(data["explanation"]),
    )


def trace_to_dict(trace: TwinTrace) -> dict[str, Any]:
    parameters = {
        name: getattr(trace.parameters, name)
        for name in trace.parameters.__dataclass_fields__
    }
    version = {
        name: getattr(trace.version, name)
        for name in trace.version.__dataclass_fields__
    }
    steps = []
    for step in trace.steps:
        steps.append(
            {
                "index": step.index,
                "started_at": step.started_at.isoformat(),
                "ended_at": step.ended_at.isoformat(),
                "duration_hours": step.duration_hours,
                "prior_state": _state_to_dict(step.prior_state),
                "next_state": _state_to_dict(step.next_state),
                "requested_control": _control_to_dict(step.requested_control),
                "disturbance": _disturbance_to_dict(step.disturbance),
                "correction": _correction_to_dict(step.correction),
                "actual_battery_power_kw": step.actual_battery_power_kw,
                "actual_ev_charge_kw": step.actual_ev_charge_kw,
                "hvac_electric_kw": step.hvac_electric_kw,
                "effective_base_load_kw": step.effective_base_load_kw,
                "available_pv_kw": step.available_pv_kw,
                "curtailed_pv_kw": step.curtailed_pv_kw,
                "grid_power_kw": step.grid_power_kw,
                "thermal_loss_kw": step.thermal_loss_kw,
                "net_thermal_kw": step.net_thermal_kw,
                "violations": [
                    {
                        "code": violation.code.value,
                        "magnitude": violation.magnitude,
                        "message": violation.message,
                    }
                    for violation in step.violations
                ],
            }
        )
    return {
        "trace_id": trace.trace_id,
        "generated_at": trace.generated_at.isoformat(),
        "parameters": parameters,
        "version": version,
        "initial_state": _state_to_dict(trace.initial_state),
        "steps": steps,
        "final_state": _state_to_dict(trace.final_state),
        "explanation": trace.explanation,
        "metadata": [list(item) for item in trace.metadata],
    }


def trace_from_dict(data: Mapping[str, Any]) -> TwinTrace:
    raw_steps = data["steps"]
    if not isinstance(raw_steps, list):
        raise TypeError("steps must be a list")
    steps: list[TwinStepResult] = []
    for raw in raw_steps:
        if not isinstance(raw, Mapping):
            raise TypeError("each step must be a mapping")
        raw_violations = raw["violations"]
        if not isinstance(raw_violations, list):
            raise TypeError("violations must be a list")
        violations = tuple(
            ConstraintViolation(
                code=ConstraintCode(str(item["code"])),
                magnitude=float(item["magnitude"]),
                message=str(item["message"]),
            )
            for item in raw_violations
        )
        steps.append(
            TwinStepResult(
                index=int(raw["index"]),
                started_at=datetime.fromisoformat(str(raw["started_at"])),
                ended_at=datetime.fromisoformat(str(raw["ended_at"])),
                duration_hours=float(raw["duration_hours"]),
                prior_state=_state_from_dict(raw["prior_state"]),
                next_state=_state_from_dict(raw["next_state"]),
                requested_control=_control_from_dict(raw["requested_control"]),
                disturbance=_disturbance_from_dict(raw["disturbance"]),
                correction=_correction_from_dict(raw["correction"]),
                actual_battery_power_kw=float(raw["actual_battery_power_kw"]),
                actual_ev_charge_kw=float(raw["actual_ev_charge_kw"]),
                hvac_electric_kw=float(raw["hvac_electric_kw"]),
                effective_base_load_kw=float(raw["effective_base_load_kw"]),
                available_pv_kw=float(raw["available_pv_kw"]),
                curtailed_pv_kw=float(raw["curtailed_pv_kw"]),
                grid_power_kw=float(raw["grid_power_kw"]),
                thermal_loss_kw=float(raw["thermal_loss_kw"]),
                net_thermal_kw=float(raw["net_thermal_kw"]),
                violations=violations,
            )
        )
    raw_metadata = data.get("metadata", [])
    return TwinTrace(
        trace_id=str(data["trace_id"]),
        generated_at=datetime.fromisoformat(str(data["generated_at"])),
        parameters=TwinParameters(**dict(data["parameters"])),
        version=TwinVersion(**dict(data["version"])),
        initial_state=_state_from_dict(data["initial_state"]),
        steps=tuple(steps),
        final_state=_state_from_dict(data["final_state"]),
        explanation=str(data["explanation"]),
        metadata=tuple((str(item[0]), str(item[1])) for item in raw_metadata),
    )


def dumps_trace(trace: TwinTrace) -> str:
    return json.dumps(trace_to_dict(trace), sort_keys=True, separators=(",", ":"))


def loads_trace(payload: str) -> TwinTrace:
    data = json.loads(payload)
    if not isinstance(data, Mapping):
        raise TypeError("trace JSON must contain an object")
    return trace_from_dict(data)

