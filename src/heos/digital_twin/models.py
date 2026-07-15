from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from math import isfinite


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _non_negative(value: float, name: str) -> float:
    number = _finite(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return number


def _positive(value: float, name: str) -> float:
    number = _finite(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def _fraction(value: float, name: str) -> float:
    number = _finite(value, name)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return number


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _text(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class TwinVersion:
    schema_version: str = "digital-twin-1"
    model_version: str = "physics-1"
    parameter_version: str = "parameters-1"
    correction_version: str = "none"

    def __post_init__(self) -> None:
        for name in (
            "schema_version",
            "model_version",
            "parameter_version",
            "correction_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class TwinParameters:
    thermal_capacity_kwh_per_c: float
    heat_loss_kw_per_c: float
    hvac_cop: float
    battery_capacity_kwh: float
    battery_max_charge_kw: float
    battery_max_discharge_kw: float
    battery_charge_efficiency: float = 0.95
    battery_discharge_efficiency: float = 0.95
    ev_capacity_kwh: float = 1.0
    ev_max_charge_kw: float = 0.0
    ev_charge_efficiency: float = 0.92
    grid_max_import_kw: float = 17.25
    grid_max_export_kw: float = 10.0
    indoor_min_c: float = 5.0
    indoor_max_c: float = 35.0
    version: str = "parameters-1"

    def __post_init__(self) -> None:
        for name in (
            "thermal_capacity_kwh_per_c",
            "hvac_cop",
            "battery_capacity_kwh",
            "ev_capacity_kwh",
        ):
            object.__setattr__(self, name, _positive(getattr(self, name), name))
        for name in (
            "heat_loss_kw_per_c",
            "battery_max_charge_kw",
            "battery_max_discharge_kw",
            "ev_max_charge_kw",
            "grid_max_import_kw",
            "grid_max_export_kw",
        ):
            object.__setattr__(self, name, _non_negative(getattr(self, name), name))
        for name in (
            "battery_charge_efficiency",
            "battery_discharge_efficiency",
            "ev_charge_efficiency",
        ):
            value = _fraction(getattr(self, name), name)
            if value == 0.0:
                raise ValueError(f"{name} must be greater than zero")
            object.__setattr__(self, name, value)
        minimum = _finite(self.indoor_min_c, "indoor_min_c")
        maximum = _finite(self.indoor_max_c, "indoor_max_c")
        if maximum <= minimum:
            raise ValueError("indoor_max_c must be greater than indoor_min_c")
        object.__setattr__(self, "indoor_min_c", minimum)
        object.__setattr__(self, "indoor_max_c", maximum)
        object.__setattr__(self, "version", _text(self.version, "version"))


@dataclass(frozen=True, slots=True)
class TwinState:
    observed_at: datetime
    indoor_temp_c: float
    battery_soc: float
    ev_soc: float = 0.0
    grid_import_kwh: float = 0.0
    grid_export_kwh: float = 0.0
    battery_throughput_kwh: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _aware(self.observed_at, "observed_at"))
        object.__setattr__(self, "indoor_temp_c", _finite(self.indoor_temp_c, "indoor_temp_c"))
        object.__setattr__(self, "battery_soc", _fraction(self.battery_soc, "battery_soc"))
        object.__setattr__(self, "ev_soc", _fraction(self.ev_soc, "ev_soc"))
        for name in (
            "grid_import_kwh",
            "grid_export_kwh",
            "battery_throughput_kwh",
        ):
            object.__setattr__(self, name, _non_negative(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class TwinControl:
    hvac_thermal_kw: float = 0.0
    battery_power_kw: float = 0.0
    ev_charge_kw: float = 0.0
    pv_curtailment_kw: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "hvac_thermal_kw", _finite(self.hvac_thermal_kw, "hvac_thermal_kw"))
        object.__setattr__(self, "battery_power_kw", _finite(self.battery_power_kw, "battery_power_kw"))
        object.__setattr__(self, "ev_charge_kw", _non_negative(self.ev_charge_kw, "ev_charge_kw"))
        object.__setattr__(
            self,
            "pv_curtailment_kw",
            _non_negative(self.pv_curtailment_kw, "pv_curtailment_kw"),
        )


@dataclass(frozen=True, slots=True)
class TwinDisturbance:
    outdoor_temp_c: float
    pv_kw: float
    base_load_kw: float
    solar_gain_kw: float = 0.0
    internal_gain_kw: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "outdoor_temp_c", _finite(self.outdoor_temp_c, "outdoor_temp_c"))
        object.__setattr__(self, "pv_kw", _non_negative(self.pv_kw, "pv_kw"))
        object.__setattr__(self, "base_load_kw", _non_negative(self.base_load_kw, "base_load_kw"))
        object.__setattr__(self, "solar_gain_kw", _finite(self.solar_gain_kw, "solar_gain_kw"))
        object.__setattr__(self, "internal_gain_kw", _finite(self.internal_gain_kw, "internal_gain_kw"))


@dataclass(frozen=True, slots=True)
class CorrectionVector:
    indoor_temp_delta_c: float = 0.0
    base_load_delta_kw: float = 0.0
    pv_delta_kw: float = 0.0
    source: str = "none"
    explanation: str = "No residual correction applied."

    def __post_init__(self) -> None:
        for name in ("indoor_temp_delta_c", "base_load_delta_kw", "pv_delta_kw"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        object.__setattr__(self, "source", _text(self.source, "source"))
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))


class ConstraintCode(StrEnum):
    BATTERY_POWER_LIMITED = "battery_power_limited"
    EV_POWER_LIMITED = "ev_power_limited"
    PV_CURTAILMENT_LIMITED = "pv_curtailment_limited"
    GRID_IMPORT_LIMIT = "grid_import_limit"
    GRID_EXPORT_LIMIT = "grid_export_limit"
    INDOOR_TEMPERATURE_LOW = "indoor_temperature_low"
    INDOOR_TEMPERATURE_HIGH = "indoor_temperature_high"


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    code: ConstraintCode
    magnitude: float
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "magnitude", _non_negative(self.magnitude, "magnitude"))
        object.__setattr__(self, "message", _text(self.message, "message"))


@dataclass(frozen=True, slots=True)
class TwinStepResult:
    index: int
    started_at: datetime
    ended_at: datetime
    duration_hours: float
    prior_state: TwinState
    next_state: TwinState
    requested_control: TwinControl
    disturbance: TwinDisturbance
    correction: CorrectionVector
    actual_battery_power_kw: float
    actual_ev_charge_kw: float
    hvac_electric_kw: float
    effective_base_load_kw: float
    available_pv_kw: float
    curtailed_pv_kw: float
    grid_power_kw: float
    thermal_loss_kw: float
    net_thermal_kw: float
    violations: tuple[ConstraintViolation, ...] = ()

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("index must be non-negative")
        object.__setattr__(self, "started_at", _aware(self.started_at, "started_at"))
        object.__setattr__(self, "ended_at", _aware(self.ended_at, "ended_at"))
        if self.ended_at <= self.started_at:
            raise ValueError("ended_at must be after started_at")
        object.__setattr__(self, "duration_hours", _positive(self.duration_hours, "duration_hours"))
        for name in (
            "actual_battery_power_kw",
            "actual_ev_charge_kw",
            "hvac_electric_kw",
            "effective_base_load_kw",
            "available_pv_kw",
            "curtailed_pv_kw",
            "grid_power_kw",
            "thermal_loss_kw",
            "net_thermal_kw",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        object.__setattr__(self, "violations", tuple(self.violations))

    @property
    def grid_import_kw(self) -> float:
        return max(0.0, self.grid_power_kw)

    @property
    def grid_export_kw(self) -> float:
        return max(0.0, -self.grid_power_kw)

    @property
    def feasible(self) -> bool:
        return not self.violations


@dataclass(frozen=True, slots=True)
class TwinTrace:
    trace_id: str
    generated_at: datetime
    parameters: TwinParameters
    version: TwinVersion
    initial_state: TwinState
    steps: tuple[TwinStepResult, ...]
    final_state: TwinState
    explanation: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace_id", _text(self.trace_id, "trace_id"))
        object.__setattr__(self, "generated_at", _aware(self.generated_at, "generated_at"))
        steps = tuple(self.steps)
        if not steps:
            raise ValueError("steps must not be empty")
        object.__setattr__(self, "steps", steps)
        if steps[0].prior_state != self.initial_state:
            raise ValueError("first step must start from initial_state")
        if steps[-1].next_state != self.final_state:
            raise ValueError("final_state must equal the last step next_state")
        for previous, current in zip(steps, steps[1:], strict=False):
            if previous.next_state != current.prior_state:
                raise ValueError("steps must form a continuous state chain")
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        normalized = tuple(sorted((_text(k, "metadata key"), str(v)) for k, v in self.metadata))
        object.__setattr__(self, "metadata", normalized)

    @property
    def feasible(self) -> bool:
        return all(step.feasible for step in self.steps)

    @property
    def total_grid_import_kwh(self) -> float:
        return self.final_state.grid_import_kwh - self.initial_state.grid_import_kwh

    @property
    def total_grid_export_kwh(self) -> float:
        return self.final_state.grid_export_kwh - self.initial_state.grid_export_kwh
