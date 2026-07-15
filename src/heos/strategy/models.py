from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from heos.digital_twin import TwinControl, TwinDisturbance, TwinState, TwinTrace


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


class StrategyObjective(StrEnum):
    BALANCED = "balanced"
    SELF_CONSUMPTION = "self_consumption"
    COST = "cost"
    COMFORT = "comfort"
    RESERVE = "reserve"
    EV_PRIORITY = "ev_priority"


@dataclass(frozen=True, slots=True)
class TariffStep:
    import_price_per_kwh: float
    export_price_per_kwh: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "import_price_per_kwh",
            _non_negative(self.import_price_per_kwh, "import_price_per_kwh"),
        )
        object.__setattr__(
            self,
            "export_price_per_kwh",
            _non_negative(self.export_price_per_kwh, "export_price_per_kwh"),
        )


@dataclass(frozen=True, slots=True)
class ComfortBand:
    minimum_c: float
    maximum_c: float

    def __post_init__(self) -> None:
        minimum = _finite(self.minimum_c, "minimum_c")
        maximum = _finite(self.maximum_c, "maximum_c")
        if maximum <= minimum:
            raise ValueError("maximum_c must be greater than minimum_c")
        object.__setattr__(self, "minimum_c", minimum)
        object.__setattr__(self, "maximum_c", maximum)

    @property
    def midpoint_c(self) -> float:
        return (self.minimum_c + self.maximum_c) / 2.0


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    candidate_id: str
    name: str
    controls: tuple[TwinControl, ...]
    objective: StrategyObjective = StrategyObjective.BALANCED
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _text(self.candidate_id, "candidate_id"))
        object.__setattr__(self, "name", _text(self.name, "name"))
        controls = tuple(self.controls)
        if not controls:
            raise ValueError("controls must not be empty")
        object.__setattr__(self, "controls", controls)
        normalized_tags = tuple(sorted({_text(item, "tag") for item in self.tags}))
        object.__setattr__(self, "tags", normalized_tags)


@dataclass(frozen=True, slots=True)
class StrategyRequest:
    initial_state: TwinState
    disturbances: tuple[TwinDisturbance, ...]
    tariffs: tuple[TariffStep, ...]
    comfort_bands: tuple[ComfortBand, ...]
    step_duration: timedelta
    generated_at: datetime
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        disturbances = tuple(self.disturbances)
        if not disturbances:
            raise ValueError("disturbances must not be empty")
        object.__setattr__(self, "disturbances", disturbances)
        tariffs = tuple(self.tariffs)
        if len(tariffs) not in {1, len(disturbances)}:
            raise ValueError("tariffs must contain one item or match the horizon")
        object.__setattr__(self, "tariffs", tariffs)
        bands = tuple(self.comfort_bands)
        if len(bands) not in {1, len(disturbances)}:
            raise ValueError("comfort_bands must contain one item or match the horizon")
        object.__setattr__(self, "comfort_bands", bands)
        if self.step_duration.total_seconds() <= 0.0:
            raise ValueError("step_duration must be greater than zero")
        object.__setattr__(self, "generated_at", _aware(self.generated_at, "generated_at"))
        normalized = tuple(sorted((_text(key, "metadata key"), str(value)) for key, value in self.metadata))
        object.__setattr__(self, "metadata", normalized)

    @property
    def horizon(self) -> int:
        return len(self.disturbances)

    @property
    def expanded_tariffs(self) -> tuple[TariffStep, ...]:
        if len(self.tariffs) == 1:
            return self.tariffs * self.horizon
        return self.tariffs

    @property
    def expanded_comfort_bands(self) -> tuple[ComfortBand, ...]:
        if len(self.comfort_bands) == 1:
            return self.comfort_bands * self.horizon
        return self.comfort_bands


@dataclass(frozen=True, slots=True)
class StrategyPolicy:
    energy_cost_weight: float = 1.0
    peak_import_weight: float = 0.10
    battery_throughput_weight: float = 0.03
    comfort_deviation_weight: float = 4.0
    ev_shortfall_weight: float = 12.0
    battery_reserve_shortfall_weight: float = 8.0
    violation_count_weight: float = 1000.0
    violation_magnitude_weight: float = 100.0
    target_ev_soc: float = 0.0
    reserve_battery_soc: float = 0.0
    require_feasible: bool = True
    version: str = "strategy-policy-1"

    def __post_init__(self) -> None:
        weight_names = (
            "energy_cost_weight",
            "peak_import_weight",
            "battery_throughput_weight",
            "comfort_deviation_weight",
            "ev_shortfall_weight",
            "battery_reserve_shortfall_weight",
            "violation_count_weight",
            "violation_magnitude_weight",
        )
        total = 0.0
        for name in weight_names:
            value = _non_negative(getattr(self, name), name)
            object.__setattr__(self, name, value)
            total += value
        if total <= 0.0:
            raise ValueError("at least one strategy weight must be positive")
        object.__setattr__(self, "target_ev_soc", _fraction(self.target_ev_soc, "target_ev_soc"))
        object.__setattr__(
            self,
            "reserve_battery_soc",
            _fraction(self.reserve_battery_soc, "reserve_battery_soc"),
        )
        object.__setattr__(self, "version", _text(self.version, "version"))


@dataclass(frozen=True, slots=True)
class StrategyMetrics:
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    net_energy_cost: float
    peak_grid_import_kw: float
    battery_throughput_kwh: float
    comfort_deviation_degree_hours: float
    ev_shortfall: float
    battery_reserve_shortfall: float
    violation_count: int
    violation_magnitude: float
    objective_score: float

    def __post_init__(self) -> None:
        for name in (
            "total_grid_import_kwh",
            "total_grid_export_kwh",
            "peak_grid_import_kw",
            "battery_throughput_kwh",
            "comfort_deviation_degree_hours",
            "ev_shortfall",
            "battery_reserve_shortfall",
            "violation_magnitude",
        ):
            object.__setattr__(self, name, _non_negative(getattr(self, name), name))
        object.__setattr__(self, "net_energy_cost", _finite(self.net_energy_cost, "net_energy_cost"))
        object.__setattr__(self, "objective_score", _finite(self.objective_score, "objective_score"))
        if self.violation_count < 0:
            raise ValueError("violation_count must be non-negative")


@dataclass(frozen=True, slots=True)
class StrategyEvaluation:
    candidate: StrategyCandidate
    trace: TwinTrace
    metrics: StrategyMetrics
    feasible: bool
    rank: int
    explanation: str

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError("rank must be positive")
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    decision_id: str
    generated_at: datetime
    selected: StrategyEvaluation
    alternatives: tuple[StrategyEvaluation, ...]
    policy_version: str
    parameter_version: str
    explanation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id"))
        object.__setattr__(self, "generated_at", _aware(self.generated_at, "generated_at"))
        alternatives = tuple(self.alternatives)
        if not alternatives:
            raise ValueError("alternatives must not be empty")
        ids = [item.candidate.candidate_id for item in alternatives]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate ids must be unique")
        ranks = [item.rank for item in alternatives]
        if ranks != list(range(1, len(alternatives) + 1)):
            raise ValueError("alternatives must be ordered by contiguous rank")
        if alternatives[0] != self.selected or self.selected.rank != 1:
            raise ValueError("selected must be the rank-one alternative")
        object.__setattr__(self, "alternatives", alternatives)
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        object.__setattr__(self, "parameter_version", _text(self.parameter_version, "parameter_version"))
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
