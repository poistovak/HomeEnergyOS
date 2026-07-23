from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    decision: str
    confidence: float


class ReasoningOrchestrator:

    def create_result(
        self,
        decision: str,
        confidence: float,
    ) -> ReasoningResult:

        if not decision.strip():
            raise ValueError(
                "decision must not be empty"
            )

        if not 0 <= confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        return ReasoningResult(
            decision=decision,
            confidence=confidence,
        )