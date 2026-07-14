"""Immutable arbitration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from heos.planning.models import FutureScenario


@dataclass(frozen=True, slots=True)
class ArbitrationCandidate:
    scenario: FutureScenario
    policy_priority: int = 0
    valid: bool = True
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.valid and not self.rejection_reason:
            raise ValueError(
                "invalid candidate requires rejection_reason"
            )


@dataclass(frozen=True, slots=True)
class CandidateRanking:
    scenario_id: str
    rank: int
    scenario_score: float
    policy_priority: int
    confidence: float
    valid: bool
    reason: str


@dataclass(frozen=True, slots=True)
class DecisionTraceEntry:
    stage: str
    message: str


@dataclass(frozen=True, slots=True)
class ArbitrationReport:
    winner: FutureScenario | None
    ranking: tuple[CandidateRanking, ...]
    trace: tuple[DecisionTraceEntry, ...]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def winner_id(self) -> str | None:
        if self.winner is None:
            return None
        return self.winner.scenario_id

    @property
    def decided(self) -> bool:
        return self.winner is not None
