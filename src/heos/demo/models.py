from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping


def _text(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


@dataclass(frozen=True, slots=True)
class DemoStage:
    name: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "name"))
        normalized = _text(self.status, "status").lower()
        if normalized not in {"pass", "fail"}:
            raise ValueError("status must be pass or fail")
        object.__setattr__(self, "status", normalized)
        object.__setattr__(self, "detail", _text(self.detail, "detail"))

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class DemoResult:
    demo_version: str
    scenario_id: str
    generated_at: datetime
    success: bool
    selected_strategy: str
    strategy_decision_id: str
    alternative_scores: tuple[tuple[str, float], ...]
    release_id: str
    release_status: str
    certificate_id: str
    proof_valid: bool
    replay_token: str
    compiler_scenario: str
    execution_steps: tuple[str, ...]
    safety_verdict: str
    execution_status: str
    execution_messages: tuple[str, ...]
    feedback_classification: str
    feedback_score: float
    memory_record_id: str
    memory_fingerprint: str
    memory_quality: float
    stages: tuple[DemoStage, ...]
    audit_digest: str
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        for name in (
            "demo_version",
            "scenario_id",
            "selected_strategy",
            "strategy_decision_id",
            "release_id",
            "release_status",
            "certificate_id",
            "replay_token",
            "compiler_scenario",
            "safety_verdict",
            "execution_status",
            "feedback_classification",
            "memory_record_id",
            "memory_fingerprint",
            "audit_digest",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "generated_at", _aware(self.generated_at, "generated_at"))
        object.__setattr__(
            self,
            "alternative_scores",
            tuple(sorted((str(name), float(score)) for name, score in self.alternative_scores)),
        )
        object.__setattr__(self, "execution_steps", tuple(str(item) for item in self.execution_steps))
        object.__setattr__(
            self,
            "execution_messages",
            tuple(str(item) for item in self.execution_messages),
        )
        stages = tuple(self.stages)
        if not stages:
            raise ValueError("stages must not be empty")
        object.__setattr__(self, "stages", stages)
        for name in ("feedback_score", "memory_quality"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
            object.__setattr__(self, name, value)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(sorted((str(k), str(v)) for k, v in self.metadata.items()))),
        )

    @property
    def failed_stages(self) -> tuple[DemoStage, ...]:
        return tuple(stage for stage in self.stages if not stage.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "demo_version": self.demo_version,
            "scenario_id": self.scenario_id,
            "generated_at": self.generated_at.isoformat(),
            "success": self.success,
            "selected_strategy": self.selected_strategy,
            "strategy_decision_id": self.strategy_decision_id,
            "alternative_scores": [
                {"candidate_id": name, "objective_score": score}
                for name, score in self.alternative_scores
            ],
            "release_id": self.release_id,
            "release_status": self.release_status,
            "certificate_id": self.certificate_id,
            "proof_valid": self.proof_valid,
            "replay_token": self.replay_token,
            "compiler_scenario": self.compiler_scenario,
            "execution_steps": list(self.execution_steps),
            "safety_verdict": self.safety_verdict,
            "execution_status": self.execution_status,
            "execution_messages": list(self.execution_messages),
            "feedback_classification": self.feedback_classification,
            "feedback_score": self.feedback_score,
            "memory_record_id": self.memory_record_id,
            "memory_fingerprint": self.memory_fingerprint,
            "memory_quality": self.memory_quality,
            "stages": [stage.to_dict() for stage in self.stages],
            "audit_digest": self.audit_digest,
            "metadata": dict(self.metadata),
        }
