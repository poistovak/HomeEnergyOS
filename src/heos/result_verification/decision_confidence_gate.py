from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .reasoning_orchestrator import ReasoningResult


class ConfidenceGateStatus(StrEnum):
    ACCEPT = "ACCEPT"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True, slots=True)
class ConfidenceGateDecision:
    decision: str
    confidence: float
    status: ConfidenceGateStatus
    reason: str

    @property
    def accepted(self) -> bool:
        return self.status is ConfidenceGateStatus.ACCEPT


@dataclass(frozen=True, slots=True)
class DecisionConfidenceGate:
    minimum_confidence: float = 0.6

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between 0 and 1"
            )

    def evaluate(
        self,
        result: ReasoningResult,
    ) -> ConfidenceGateDecision:
        if result.confidence >= self.minimum_confidence:
            return ConfidenceGateDecision(
                decision=result.decision,
                confidence=result.confidence,
                status=ConfidenceGateStatus.ACCEPT,
                reason="reasoning confidence meets required threshold",
            )

        return ConfidenceGateDecision(
            decision=result.decision,
            confidence=result.confidence,
            status=ConfidenceGateStatus.ABSTAIN,
            reason="insufficient evidence for autonomous decision",
        )