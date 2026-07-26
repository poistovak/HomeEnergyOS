from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .decision_confidence_gate import (
    ConfidenceGateDecision,
    ConfidenceGateStatus,
    DecisionConfidenceGate,
)
from .reasoning_orchestrator import ReasoningResult


class AutonomyAdmissionStatus(StrEnum):
    ADMITTED = "ADMITTED"
    ABSTAINED = "ABSTAINED"


@dataclass(frozen=True, slots=True)
class AutonomyAdmission:
    decision: str
    confidence: float
    status: AutonomyAdmissionStatus
    reason: str

    @property
    def admitted(self) -> bool:
        return self.status is AutonomyAdmissionStatus.ADMITTED


@dataclass(frozen=True, slots=True)
class AutonomyAdmissionGate:
    confidence_gate: DecisionConfidenceGate

    def evaluate(
        self,
        result: ReasoningResult,
    ) -> AutonomyAdmission:
        confidence_decision: ConfidenceGateDecision = (
            self.confidence_gate.evaluate(result)
        )

        if confidence_decision.status is ConfidenceGateStatus.ABSTAIN:
            return AutonomyAdmission(
                decision=result.decision,
                confidence=result.confidence,
                status=AutonomyAdmissionStatus.ABSTAINED,
                reason=confidence_decision.reason,
            )

        return AutonomyAdmission(
            decision=result.decision,
            confidence=result.confidence,
            status=AutonomyAdmissionStatus.ADMITTED,
            reason="reasoning admitted to operational release evaluation",
        )