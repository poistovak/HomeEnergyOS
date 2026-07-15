from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from typing import Any


def _text(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


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


class OperationMode(StrEnum):
    OBSERVE = "observe"
    ADVISE = "advise"
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"


_MODE_RANK = {
    OperationMode.OBSERVE: 0,
    OperationMode.ADVISE: 1,
    OperationMode.SUPERVISED: 2,
    OperationMode.AUTONOMOUS: 3,
}


def mode_rank(mode: OperationMode) -> int:
    return _MODE_RANK[OperationMode(mode)]


class ReleaseStatus(StrEnum):
    RELEASED = "released"
    HELD = "held"
    REJECTED = "rejected"


class GateCode(StrEnum):
    MANIFEST_COMPLETE = "manifest_complete"
    MODE_ALLOWED = "mode_allowed"
    DECISION_SHAPE = "decision_shape"
    DECISION_FRESH = "decision_fresh"
    STRATEGY_FEASIBLE = "strategy_feasible"
    STRATEGY_SCORE = "strategy_score"
    ZERO_VIOLATIONS = "zero_violations"
    OBJECTIVE_ALLOWED = "objective_allowed"
    POLICY_VERSION_ALLOWED = "policy_version_allowed"
    PARAMETER_VERSION_ALLOWED = "parameter_version_allowed"
    FORECAST_READY = "forecast_ready"
    FEEDBACK_READY = "feedback_ready"
    MEMORY_READY = "memory_ready"
    DIGITAL_TWIN_READY = "digital_twin_ready"
    CALIBRATION_READY = "calibration_ready"
    STRATEGY_READY = "strategy_ready"
    COMPILER_READY = "compiler_ready"
    SAFETY_READY = "safety_ready"
    EXECUTOR_READY = "executor_ready"
    OPERATOR_APPROVAL = "operator_approval"
    AUTONOMY_AUTHORIZATION = "autonomy_authorization"


REQUIRED_COMPONENTS = (
    "forecast",
    "feedback",
    "memory",
    "digital_twin",
    "calibration",
    "strategy",
    "compiler",
    "safety",
    "execution",
)


@dataclass(frozen=True, slots=True)
class ComponentVersion:
    component: str
    version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "component", _text(self.component, "component"))
        object.__setattr__(self, "version", _text(self.version, "version"))


@dataclass(frozen=True, slots=True)
class SystemManifest:
    components: tuple[ComponentVersion, ...]
    built_at: datetime
    schema_version: str = "heos-release-manifest-1"

    def __post_init__(self) -> None:
        components = tuple(self.components)
        names = [item.component for item in components]
        if len(names) != len(set(names)):
            raise ValueError("component names must be unique")
        object.__setattr__(self, "components", tuple(sorted(components, key=lambda item: item.component)))
        object.__setattr__(self, "built_at", _aware(self.built_at, "built_at"))
        object.__setattr__(self, "schema_version", _text(self.schema_version, "schema_version"))

    @property
    def versions(self) -> tuple[tuple[str, str], ...]:
        return tuple((item.component, item.version) for item in self.components)

    @property
    def missing_required_components(self) -> tuple[str, ...]:
        present = {item.component for item in self.components}
        return tuple(name for name in REQUIRED_COMPONENTS if name not in present)

    @property
    def complete(self) -> bool:
        return not self.missing_required_components


@dataclass(frozen=True, slots=True)
class ReadinessEvidence:
    forecast_ready: bool = True
    feedback_ready: bool = True
    memory_ready: bool = True
    digital_twin_ready: bool = True
    calibration_ready: bool = True
    strategy_ready: bool = True
    compiler_ready: bool = True
    safety_ready: bool = True
    executor_ready: bool = True

    def as_pairs(self) -> tuple[tuple[str, bool], ...]:
        return (
            ("forecast", self.forecast_ready),
            ("feedback", self.feedback_ready),
            ("memory", self.memory_ready),
            ("digital_twin", self.digital_twin_ready),
            ("calibration", self.calibration_ready),
            ("strategy", self.strategy_ready),
            ("compiler", self.compiler_ready),
            ("safety", self.safety_ready),
            ("executor", self.executor_ready),
        )

    @property
    def all_ready(self) -> bool:
        return all(value for _, value in self.as_pairs())


@dataclass(frozen=True, slots=True)
class ReleasePolicy:
    maximum_mode: OperationMode = OperationMode.ADVISE
    maximum_decision_age: timedelta = timedelta(minutes=15)
    maximum_future_skew: timedelta = timedelta(seconds=30)
    maximum_objective_score: float | None = None
    require_feasible: bool = True
    require_zero_violations: bool = True
    minimum_alternatives: int = 1
    allowed_objectives: tuple[str, ...] = ()
    allowed_policy_versions: tuple[str, ...] = ()
    allowed_parameter_versions: tuple[str, ...] = ()
    require_operator_approval_for_supervised: bool = True
    require_operator_approval_for_autonomous: bool = True
    version: str = "release-policy-1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "maximum_mode", OperationMode(self.maximum_mode))
        if self.maximum_decision_age.total_seconds() <= 0:
            raise ValueError("maximum_decision_age must be positive")
        if self.maximum_future_skew.total_seconds() < 0:
            raise ValueError("maximum_future_skew must be non-negative")
        if self.maximum_objective_score is not None:
            object.__setattr__(
                self,
                "maximum_objective_score",
                _finite(self.maximum_objective_score, "maximum_objective_score"),
            )
        if self.minimum_alternatives < 1:
            raise ValueError("minimum_alternatives must be at least one")
        for name in (
            "allowed_objectives",
            "allowed_policy_versions",
            "allowed_parameter_versions",
        ):
            values = tuple(sorted({_text(item, name) for item in getattr(self, name)}))
            object.__setattr__(self, name, values)
        object.__setattr__(self, "version", _text(self.version, "version"))


@dataclass(frozen=True, slots=True)
class OperationalRequest:
    strategy_decision: Any
    requested_mode: OperationMode
    evaluated_at: datetime
    manifest: SystemManifest
    readiness: ReadinessEvidence = field(default_factory=ReadinessEvidence)
    operator_approved: bool = False
    autonomy_authorized: bool = False
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_mode", OperationMode(self.requested_mode))
        object.__setattr__(self, "evaluated_at", _aware(self.evaluated_at, "evaluated_at"))
        normalized = tuple(
            sorted((_text(key, "metadata key"), str(value)) for key, value in self.metadata)
        )
        object.__setattr__(self, "metadata", normalized)


@dataclass(frozen=True, slots=True)
class GateResult:
    code: GateCode
    passed: bool
    critical: bool
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", GateCode(self.code))
        object.__setattr__(self, "detail", _text(self.detail, "detail"))


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    intent_id: str
    source_decision_id: str
    candidate_id: str
    requested_mode: OperationMode
    created_at: datetime
    not_after: datetime
    compiler_target: str
    control_payload: tuple[tuple[str, float], ...]
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "intent_id", _text(self.intent_id, "intent_id"))
        object.__setattr__(
            self, "source_decision_id", _text(self.source_decision_id, "source_decision_id")
        )
        object.__setattr__(self, "candidate_id", _text(self.candidate_id, "candidate_id"))
        object.__setattr__(self, "requested_mode", OperationMode(self.requested_mode))
        created = _aware(self.created_at, "created_at")
        not_after = _aware(self.not_after, "not_after")
        if not_after <= created:
            raise ValueError("not_after must be after created_at")
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "not_after", not_after)
        object.__setattr__(self, "compiler_target", _text(self.compiler_target, "compiler_target"))
        payload = tuple(sorted((_text(key, "control key"), _finite(value, key)) for key, value in self.control_payload))
        if not payload:
            raise ValueError("control_payload must not be empty")
        object.__setattr__(self, "control_payload", payload)
        normalized = tuple(
            sorted((_text(key, "metadata key"), str(value)) for key, value in self.metadata)
        )
        object.__setattr__(self, "metadata", normalized)


@dataclass(frozen=True, slots=True)
class ReleaseDecision:
    release_id: str
    source_decision_id: str
    evaluated_at: datetime
    requested_mode: OperationMode
    status: ReleaseStatus
    gates: tuple[GateResult, ...]
    policy_version: str
    manifest_schema_version: str
    intent: ExecutionIntent | None
    explanation: str
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_id", _text(self.release_id, "release_id"))
        object.__setattr__(
            self, "source_decision_id", _text(self.source_decision_id, "source_decision_id")
        )
        object.__setattr__(self, "evaluated_at", _aware(self.evaluated_at, "evaluated_at"))
        object.__setattr__(self, "requested_mode", OperationMode(self.requested_mode))
        object.__setattr__(self, "status", ReleaseStatus(self.status))
        gates = tuple(self.gates)
        if not gates:
            raise ValueError("gates must not be empty")
        object.__setattr__(self, "gates", gates)
        object.__setattr__(self, "policy_version", _text(self.policy_version, "policy_version"))
        object.__setattr__(
            self,
            "manifest_schema_version",
            _text(self.manifest_schema_version, "manifest_schema_version"),
        )
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        if self.status is ReleaseStatus.RELEASED and self.intent is None:
            raise ValueError("released decisions require an intent")
        if self.status is not ReleaseStatus.RELEASED and self.intent is not None:
            raise ValueError("held or rejected decisions must not include an intent")
        normalized = tuple(
            sorted((_text(key, "metadata key"), str(value)) for key, value in self.metadata)
        )
        object.__setattr__(self, "metadata", normalized)

    @property
    def failed_gates(self) -> tuple[GateResult, ...]:
        return tuple(item for item in self.gates if not item.passed)

    @property
    def released(self) -> bool:
        return self.status is ReleaseStatus.RELEASED
