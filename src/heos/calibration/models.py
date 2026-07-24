from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from heos.digital_twin import TwinControl, TwinDisturbance, TwinParameters, TwinState


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _positive(value: float, name: str) -> float:
    number = _finite(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def _non_negative(value: float, name: str) -> float:
    number = _finite(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return number


def _fraction(value: float, name: str) -> float:
    number = _finite(value, name)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return number


def _text(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


class CalibratableParameter(StrEnum):
    THERMAL_CAPACITY_KWH_PER_C = "thermal_capacity_kwh_per_c"
    HEAT_LOSS_KW_PER_C = "heat_loss_kw_per_c"
    HVAC_COP = "hvac_cop"
    BATTERY_CAPACITY_KWH = "battery_capacity_kwh"
    BATTERY_CHARGE_EFFICIENCY = "battery_charge_efficiency"
    BATTERY_DISCHARGE_EFFICIENCY = "battery_discharge_efficiency"
    EV_CAPACITY_KWH = "ev_capacity_kwh"
    EV_CHARGE_EFFICIENCY = "ev_charge_efficiency"

    @property
    def is_fraction(self) -> bool:
        return self in {
            CalibratableParameter.BATTERY_CHARGE_EFFICIENCY,
            CalibratableParameter.BATTERY_DISCHARGE_EFFICIENCY,
            CalibratableParameter.EV_CHARGE_EFFICIENCY,
        }


@dataclass(frozen=True, slots=True)
class CalibrationSample:
    sample_id: str
    initial_state: TwinState
    control: TwinControl
    disturbance: TwinDisturbance
    duration: timedelta
    observed_next_state: TwinState
    weight: float = 1.0
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_id", _text(self.sample_id, "sample_id"))
        seconds = self.duration.total_seconds()
        if seconds <= 0.0:
            raise ValueError("duration must be greater than zero")
        object.__setattr__(self, "weight", _positive(self.weight, "weight"))
        normalized_tags = tuple(sorted({_text(item, "tag") for item in self.tags}))
        object.__setattr__(self, "tags", normalized_tags)
        if self.observed_next_state.observed_at <= self.initial_state.observed_at:
            raise ValueError("observed_next_state must be after initial_state")

    @property
    def duration_hours(self) -> float:
        return self.duration.total_seconds() / 3600.0


@dataclass(frozen=True, slots=True)
class ParameterBounds:
    parameter: CalibratableParameter
    minimum: float
    maximum: float
    candidates: int = 9

    def __post_init__(self) -> None:
        minimum = _positive(self.minimum, "minimum")
        maximum = _positive(self.maximum, "maximum")
        if maximum <= minimum:
            raise ValueError("maximum must be greater than minimum")
        if self.parameter.is_fraction and maximum > 1.0:
            raise ValueError("fraction parameter maximum must not exceed 1")
        if self.candidates < 3 or self.candidates % 2 == 0:
            raise ValueError("candidates must be an odd integer greater than or equal to 3")
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)


@dataclass(frozen=True, slots=True)
class CalibrationMetricWeights:
    indoor_temp_c: float = 1.0
    battery_soc: float = 1.0
    ev_soc: float = 1.0
    grid_import_kwh: float = 0.5
    grid_export_kwh: float = 0.5
    battery_throughput_kwh: float = 0.25

    def __post_init__(self) -> None:
        total = 0.0
        for name in self.__dataclass_fields__:
            value = _non_negative(getattr(self, name), name)
            object.__setattr__(self, name, value)
            total += value
        if total <= 0.0:
            raise ValueError("at least one metric weight must be positive")


@dataclass(frozen=True, slots=True)
class CalibrationMetricScales:
    indoor_temp_c: float = 1.0
    battery_soc: float = 0.05
    ev_soc: float = 0.05
    grid_import_kwh: float = 1.0
    grid_export_kwh: float = 1.0
    battery_throughput_kwh: float = 1.0

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, _positive(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class CalibrationPolicy:
    rounds: int = 3
    minimum_absolute_improvement: float = 1e-6
    minimum_relative_improvement: float = 0.01
    require_validation: bool = False
    weights: CalibrationMetricWeights = field(default_factory=CalibrationMetricWeights)
    scales: CalibrationMetricScales = field(default_factory=CalibrationMetricScales)
    version: str = "calibration-policy-1"

    def __post_init__(self) -> None:
        if self.rounds < 1 or self.rounds > 12:
            raise ValueError("rounds must be between 1 and 12")
        object.__setattr__(
            self,
            "minimum_absolute_improvement",
            _non_negative(self.minimum_absolute_improvement, "minimum_absolute_improvement"),
        )
        object.__setattr__(
            self,
            "minimum_relative_improvement",
            _fraction(self.minimum_relative_improvement, "minimum_relative_improvement"),
        )
        object.__setattr__(self, "version", _text(self.version, "version"))


@dataclass(frozen=True, slots=True)
class CalibrationMetrics:
    indoor_temp_mae_c: float
    battery_soc_mae: float
    ev_soc_mae: float
    grid_import_mae_kwh: float
    grid_export_mae_kwh: float
    battery_throughput_mae_kwh: float
    weighted_loss: float
    sample_count: int
    total_weight: float

    def __post_init__(self) -> None:
        for name in (
            "indoor_temp_mae_c",
            "battery_soc_mae",
            "ev_soc_mae",
            "grid_import_mae_kwh",
            "grid_export_mae_kwh",
            "battery_throughput_mae_kwh",
            "weighted_loss",
            "total_weight",
        ):
            object.__setattr__(self, name, _non_negative(getattr(self, name), name))
        if self.sample_count < 1:
            raise ValueError("sample_count must be positive")
        if self.total_weight <= 0.0:
            raise ValueError("total_weight must be positive")


@dataclass(frozen=True, slots=True)
class ParameterEstimate:
    parameter: CalibratableParameter
    before: float
    after: float
    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        before = _positive(self.before, "before")
        after = _positive(self.after, "after")
        minimum = _positive(self.minimum, "minimum")
        maximum = _positive(self.maximum, "maximum")
        if maximum <= minimum:
            raise ValueError("maximum must be greater than minimum")
        if not minimum <= after <= maximum:
            raise ValueError("after must be within bounds")
        object.__setattr__(self, "before", before)
        object.__setattr__(self, "after", after)
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)

    @property
    def absolute_change(self) -> float:
        return self.after - self.before

    @property
    def relative_change(self) -> float:
        return (self.after - self.before) / self.before

    @property
    def at_lower_bound(self) -> bool:
        return abs(self.after - self.minimum) <= 1e-12

    @property
    def at_upper_bound(self) -> bool:
        return abs(self.after - self.maximum) <= 1e-12


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    report_id: str
    generated_at: datetime
    base_parameters: TwinParameters
    calibrated_parameters: TwinParameters
    estimates: tuple[ParameterEstimate, ...]
    training_before: CalibrationMetrics
    training_after: CalibrationMetrics
    validation_before: CalibrationMetrics | None
    validation_after: CalibrationMetrics | None
    accepted: bool
    policy_version: str
    sample_ids: tuple[str, ...]
    validation_sample_ids: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", _text(self.report_id, "report_id"))
        object.__setattr__(self, "generated_at", _aware(self.generated_at, "generated_at"))
        estimates = tuple(self.estimates)
        if not estimates:
            raise ValueError("estimates must not be empty")
        object.__setattr__(self, "estimates", estimates)
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        sample_ids = tuple(_text(item, "sample_id") for item in self.sample_ids)
        if not sample_ids:
            raise ValueError("sample_ids must not be empty")
        if len(sample_ids) != len(set(sample_ids)):
            raise ValueError("sample_ids must be unique")
        validation_ids = tuple(_text(item, "validation_sample_id") for item in self.validation_sample_ids)
        if len(validation_ids) != len(set(validation_ids)):
            raise ValueError("validation_sample_ids must be unique")
        object.__setattr__(self, "sample_ids", sample_ids)
        object.__setattr__(self, "validation_sample_ids", validation_ids)
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        if (self.validation_before is None) != (self.validation_after is None):
            raise ValueError("validation metrics must be both present or both absent")
        if bool(validation_ids) != (self.validation_before is not None):
            raise ValueError("validation sample ids must match validation metrics")

    @property
    def selection_before(self) -> CalibrationMetrics:
        return self.validation_before or self.training_before

    @property
    def selection_after(self) -> CalibrationMetrics:
        return self.validation_after or self.training_after

    @property
    def absolute_improvement(self) -> float:
        return self.selection_before.weighted_loss - self.selection_after.weighted_loss

    @property
    def relative_improvement(self) -> float:
        baseline = self.selection_before.weighted_loss
        if baseline <= 1e-15:
            return 0.0
        return self.absolute_improvement / baseline

    @property
    def recommended_parameters(self) -> TwinParameters:
        return self.calibrated_parameters if self.accepted else self.base_parameters


def ensure_unique_samples(samples: Iterable[CalibrationSample], name: str) -> tuple[CalibrationSample, ...]:
    normalized = tuple(samples)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    ids = [item.sample_id for item in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{name} sample_id values must be unique")
    return normalized
