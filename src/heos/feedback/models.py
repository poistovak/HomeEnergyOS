from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType


class ExecutionStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class OutcomeClassification(StrEnum):
    EXCELLENT = "excellent"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    FAILED = "failed"


def _require_text(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _freeze_float_mapping(values: Mapping[str, float]) -> Mapping[str, float]:
    normalized: dict[str, float] = {}
    for key, value in values.items():
        clean_key = _require_text(str(key), "mapping key")
        normalized[clean_key] = float(value)
    return MappingProxyType(dict(sorted(normalized.items())))


def _freeze_text_mapping(values: Mapping[str, str]) -> Mapping[str, str]:
    normalized = {
        _require_text(str(key), "mapping key"): str(value)
        for key, value in values.items()
    }
    return MappingProxyType(dict(sorted(normalized.items())))


@dataclass(frozen=True, slots=True)
class VersionStamp:
    schema_version: str
    forecast_version: str
    model_version: str
    policy_version: str
    compiler_version: str

    def __post_init__(self) -> None:
        for name in (
            "schema_version",
            "forecast_version",
            "model_version",
            "policy_version",
            "compiler_version",
        ):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class ActionRecord:
    resource_id: str
    action: str
    target: float | None = None
    unit: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource_id", _require_text(self.resource_id, "resource_id"))
        object.__setattr__(self, "action", _require_text(self.action, "action"))
        if self.target is not None:
            object.__setattr__(self, "target", float(self.target))
        if self.unit is not None:
            object.__setattr__(self, "unit", _require_text(self.unit, "unit"))
        object.__setattr__(self, "metadata", _freeze_text_mapping(self.metadata))

    @property
    def identity(self) -> tuple[str, str]:
        return self.resource_id, self.action


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    record_id: str
    decision_id: str
    scenario_id: str
    committed_at: datetime
    effective_from: datetime
    effective_until: datetime
    predicted_state: Mapping[str, float]
    planned_actions: tuple[ActionRecord, ...]
    versions: VersionStamp
    context: Mapping[str, str] = field(default_factory=dict)
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _require_text(self.record_id, "record_id"))
        object.__setattr__(self, "decision_id", _require_text(self.decision_id, "decision_id"))
        object.__setattr__(self, "scenario_id", _require_text(self.scenario_id, "scenario_id"))
        for name in ("committed_at", "effective_from", "effective_until"):
            object.__setattr__(self, name, _require_aware(getattr(self, name), name))
        if self.effective_until <= self.effective_from:
            raise ValueError("effective_until must be after effective_from")
        object.__setattr__(self, "predicted_state", _freeze_float_mapping(self.predicted_state))
        object.__setattr__(self, "planned_actions", tuple(self.planned_actions))
        object.__setattr__(self, "context", _freeze_text_mapping(self.context))
        if self.correlation_id is not None:
            object.__setattr__(
                self,
                "correlation_id",
                _require_text(self.correlation_id, "correlation_id"),
            )


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    record_id: str
    decision_record_id: str
    observed_at: datetime
    window_start: datetime
    window_end: datetime
    actual_state: Mapping[str, float]
    executed_actions: tuple[ActionRecord, ...]
    status: ExecutionStatus = ExecutionStatus.UNKNOWN
    constraints_satisfied: bool = True
    violations: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _require_text(self.record_id, "record_id"))
        object.__setattr__(
            self,
            "decision_record_id",
            _require_text(self.decision_record_id, "decision_record_id"),
        )
        for name in ("observed_at", "window_start", "window_end"):
            object.__setattr__(self, name, _require_aware(getattr(self, name), name))
        if self.window_end <= self.window_start:
            raise ValueError("window_end must be after window_start")
        object.__setattr__(self, "actual_state", _freeze_float_mapping(self.actual_state))
        object.__setattr__(self, "executed_actions", tuple(self.executed_actions))
        object.__setattr__(self, "violations", tuple(str(item) for item in self.violations))
        object.__setattr__(self, "notes", tuple(str(item) for item in self.notes))


@dataclass(frozen=True, slots=True)
class ComparisonMetrics:
    prediction_error: float
    execution_error: float
    timing_error: float
    constraint_error: float
    energy_error: float
    overall_score: float

    def __post_init__(self) -> None:
        for name in (
            "prediction_error",
            "execution_error",
            "timing_error",
            "constraint_error",
            "energy_error",
            "overall_score",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class ComparisonRecord:
    record_id: str
    decision_record_id: str
    outcome_record_id: str
    compared_at: datetime
    metrics: ComparisonMetrics
    classification: OutcomeClassification
    root_causes: tuple[str, ...]
    confidence: float
    explanation: str

    def __post_init__(self) -> None:
        for name in ("record_id", "decision_record_id", "outcome_record_id"):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        object.__setattr__(self, "compared_at", _require_aware(self.compared_at, "compared_at"))
        object.__setattr__(self, "root_causes", tuple(str(item) for item in self.root_causes))
        confidence = float(self.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "explanation", _require_text(self.explanation, "explanation"))


@dataclass(frozen=True, slots=True)
class ExperienceCandidate:
    record_id: str
    decision_record_id: str
    outcome_record_id: str
    comparison_record_id: str
    created_at: datetime
    features: Mapping[str, float]
    targets: Mapping[str, float]
    quality_score: float
    classification: OutcomeClassification
    versions: VersionStamp
    explanation: str

    def __post_init__(self) -> None:
        for name in (
            "record_id",
            "decision_record_id",
            "outcome_record_id",
            "comparison_record_id",
        ):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        object.__setattr__(self, "created_at", _require_aware(self.created_at, "created_at"))
        object.__setattr__(self, "features", _freeze_float_mapping(self.features))
        object.__setattr__(self, "targets", _freeze_float_mapping(self.targets))
        score = float(self.quality_score)
        if not 0.0 <= score <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")
        object.__setattr__(self, "quality_score", score)
        object.__setattr__(self, "explanation", _require_text(self.explanation, "explanation"))
