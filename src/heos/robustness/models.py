from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping


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
        raise ValueError(f"{name} must be between zero and one")
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


def _levels(values: tuple[float, ...], name: str, *, positive: bool) -> tuple[float, ...]:
    if not values:
        raise ValueError(f"{name} must not be empty")
    validator = _positive if positive else _finite
    return tuple(sorted({validator(item, name) for item in values}))


@dataclass(frozen=True, slots=True)
class Perturbation:
    pv_multiplier: float = 1.0
    load_multiplier: float = 1.0
    outdoor_temp_delta_c: float = 0.0
    tariff_multiplier: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "pv_multiplier", _positive(self.pv_multiplier, "pv_multiplier"))
        object.__setattr__(
            self,
            "load_multiplier",
            _positive(self.load_multiplier, "load_multiplier"),
        )
        object.__setattr__(
            self,
            "outdoor_temp_delta_c",
            _finite(self.outdoor_temp_delta_c, "outdoor_temp_delta_c"),
        )
        object.__setattr__(
            self,
            "tariff_multiplier",
            _positive(self.tariff_multiplier, "tariff_multiplier"),
        )

    @property
    def distance(self) -> float:
        return (
            abs(self.pv_multiplier - 1.0)
            + abs(self.load_multiplier - 1.0)
            + abs(self.outdoor_temp_delta_c) / 10.0
            + abs(self.tariff_multiplier - 1.0)
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "pv_multiplier": self.pv_multiplier,
            "load_multiplier": self.load_multiplier,
            "outdoor_temp_delta_c": self.outdoor_temp_delta_c,
            "tariff_multiplier": self.tariff_multiplier,
        }


@dataclass(frozen=True, slots=True)
class RobustnessPolicy:
    pv_multipliers: tuple[float, ...] = (0.70, 1.00, 1.30)
    load_multipliers: tuple[float, ...] = (0.85, 1.00, 1.15)
    outdoor_temp_deltas_c: tuple[float, ...] = (-3.0, 0.0, 3.0)
    tariff_multipliers: tuple[float, ...] = (0.80, 1.00, 1.20)
    min_feasible_ratio: float = 1.0
    min_selection_stability: float = 0.95
    max_regret: float = 1.0
    min_final_ev_soc: float = 0.0
    min_final_battery_soc: float = 0.0
    max_variants: int = 512
    version: str = "robustness-policy-1"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "pv_multipliers",
            _levels(self.pv_multipliers, "pv_multipliers", positive=True),
        )
        object.__setattr__(
            self,
            "load_multipliers",
            _levels(self.load_multipliers, "load_multipliers", positive=True),
        )
        object.__setattr__(
            self,
            "outdoor_temp_deltas_c",
            _levels(self.outdoor_temp_deltas_c, "outdoor_temp_deltas_c", positive=False),
        )
        object.__setattr__(
            self,
            "tariff_multipliers",
            _levels(self.tariff_multipliers, "tariff_multipliers", positive=True),
        )
        object.__setattr__(
            self,
            "min_feasible_ratio",
            _fraction(self.min_feasible_ratio, "min_feasible_ratio"),
        )
        object.__setattr__(
            self,
            "min_selection_stability",
            _fraction(self.min_selection_stability, "min_selection_stability"),
        )
        object.__setattr__(self, "max_regret", _non_negative(self.max_regret, "max_regret"))
        object.__setattr__(
            self,
            "min_final_ev_soc",
            _fraction(self.min_final_ev_soc, "min_final_ev_soc"),
        )
        object.__setattr__(
            self,
            "min_final_battery_soc",
            _fraction(self.min_final_battery_soc, "min_final_battery_soc"),
        )
        if self.max_variants < 1:
            raise ValueError("max_variants must be positive")
        object.__setattr__(self, "version", _text(self.version, "version"))

    @property
    def variant_count(self) -> int:
        return (
            len(self.pv_multipliers)
            * len(self.load_multipliers)
            * len(self.outdoor_temp_deltas_c)
            * len(self.tariff_multipliers)
        )

    @classmethod
    def quick(cls) -> RobustnessPolicy:
        return cls(
            pv_multipliers=(0.80, 1.00, 1.20),
            load_multipliers=(0.90, 1.00, 1.10),
            outdoor_temp_deltas_c=(0.0,),
            tariff_multipliers=(1.0,),
            version="robustness-policy-quick-1",
        )


@dataclass(frozen=True, slots=True)
class VariantEvaluation:
    variant_id: str
    perturbation: Perturbation
    baseline_candidate_id: str
    selected_candidate_id: str
    baseline_feasible: bool
    selected_feasible: bool
    selection_stable: bool
    baseline_score: float
    best_score: float
    regret: float
    peak_grid_import_kw: float
    final_battery_soc: float
    final_ev_soc: float
    trace_id: str

    def __post_init__(self) -> None:
        for name in (
            "variant_id",
            "baseline_candidate_id",
            "selected_candidate_id",
            "trace_id",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        for name in ("baseline_score", "best_score"):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        object.__setattr__(self, "regret", _non_negative(self.regret, "regret"))
        object.__setattr__(
            self,
            "peak_grid_import_kw",
            _non_negative(self.peak_grid_import_kw, "peak_grid_import_kw"),
        )
        object.__setattr__(
            self,
            "final_battery_soc",
            _fraction(self.final_battery_soc, "final_battery_soc"),
        )
        object.__setattr__(self, "final_ev_soc", _fraction(self.final_ev_soc, "final_ev_soc"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "perturbation": self.perturbation.to_dict(),
            "baseline_candidate_id": self.baseline_candidate_id,
            "selected_candidate_id": self.selected_candidate_id,
            "baseline_feasible": self.baseline_feasible,
            "selected_feasible": self.selected_feasible,
            "selection_stable": self.selection_stable,
            "baseline_score": self.baseline_score,
            "best_score": self.best_score,
            "regret": self.regret,
            "peak_grid_import_kw": self.peak_grid_import_kw,
            "final_battery_soc": self.final_battery_soc,
            "final_ev_soc": self.final_ev_soc,
            "trace_id": self.trace_id,
        }


@dataclass(frozen=True, slots=True)
class RobustnessSummary:
    variant_count: int
    feasible_ratio: float
    selection_stability: float
    worst_regret: float
    worst_objective_score: float
    peak_grid_import_kw: float
    minimum_final_battery_soc: float
    minimum_final_ev_soc: float

    def __post_init__(self) -> None:
        if self.variant_count < 1:
            raise ValueError("variant_count must be positive")
        object.__setattr__(
            self,
            "feasible_ratio",
            _fraction(self.feasible_ratio, "feasible_ratio"),
        )
        object.__setattr__(
            self,
            "selection_stability",
            _fraction(self.selection_stability, "selection_stability"),
        )
        object.__setattr__(self, "worst_regret", _non_negative(self.worst_regret, "worst_regret"))
        object.__setattr__(
            self,
            "worst_objective_score",
            _finite(self.worst_objective_score, "worst_objective_score"),
        )
        object.__setattr__(
            self,
            "peak_grid_import_kw",
            _non_negative(self.peak_grid_import_kw, "peak_grid_import_kw"),
        )
        object.__setattr__(
            self,
            "minimum_final_battery_soc",
            _fraction(self.minimum_final_battery_soc, "minimum_final_battery_soc"),
        )
        object.__setattr__(
            self,
            "minimum_final_ev_soc",
            _fraction(self.minimum_final_ev_soc, "minimum_final_ev_soc"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_count": self.variant_count,
            "feasible_ratio": self.feasible_ratio,
            "selection_stability": self.selection_stability,
            "worst_regret": self.worst_regret,
            "worst_objective_score": self.worst_objective_score,
            "peak_grid_import_kw": self.peak_grid_import_kw,
            "minimum_final_battery_soc": self.minimum_final_battery_soc,
            "minimum_final_ev_soc": self.minimum_final_ev_soc,
        }


@dataclass(frozen=True, slots=True)
class RobustnessCertificate:
    certificate_id: str
    generated_at: datetime
    scenario_id: str
    baseline_decision_id: str
    baseline_candidate_id: str
    strategy_policy_version: str
    parameter_version: str
    robustness_policy_version: str
    robust: bool
    reasons: tuple[str, ...]
    summary: RobustnessSummary
    variants_digest: str
    certificate_digest: str
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        for name in (
            "certificate_id",
            "scenario_id",
            "baseline_decision_id",
            "baseline_candidate_id",
            "strategy_policy_version",
            "parameter_version",
            "robustness_policy_version",
            "variants_digest",
            "certificate_digest",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "generated_at", _aware(self.generated_at, "generated_at"))
        object.__setattr__(self, "reasons", tuple(_text(item, "reason") for item in self.reasons))
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(sorted((str(k), str(v)) for k, v in self.metadata.items()))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "generated_at": self.generated_at.isoformat(),
            "scenario_id": self.scenario_id,
            "baseline_decision_id": self.baseline_decision_id,
            "baseline_candidate_id": self.baseline_candidate_id,
            "strategy_policy_version": self.strategy_policy_version,
            "parameter_version": self.parameter_version,
            "robustness_policy_version": self.robustness_policy_version,
            "robust": self.robust,
            "reasons": list(self.reasons),
            "summary": self.summary.to_dict(),
            "variants_digest": self.variants_digest,
            "certificate_digest": self.certificate_digest,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class RobustnessRun:
    certificate: RobustnessCertificate
    variants: tuple[VariantEvaluation, ...]

    def __post_init__(self) -> None:
        variants = tuple(self.variants)
        if not variants:
            raise ValueError("variants must not be empty")
        if len(variants) != self.certificate.summary.variant_count:
            raise ValueError("variant count must match certificate summary")
        object.__setattr__(self, "variants", variants)

    def to_dict(self) -> dict[str, Any]:
        return {
            "certificate": self.certificate.to_dict(),
            "variants": [item.to_dict() for item in self.variants],
        }
