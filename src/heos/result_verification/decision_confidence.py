from __future__ import annotations

from dataclasses import dataclass

from .decision_consolidation import (
    ConsolidatedDecisionMemory,
)


@dataclass(frozen=True, slots=True)
class DecisionConfidence:
    recommendation: str
    confidence: float
    samples: int


class DecisionConfidenceEngine:

    def evaluate(
        self,
        memories: list[ConsolidatedDecisionMemory],
    ) -> list[DecisionConfidence]:

        result: list[DecisionConfidence] = []

        for memory in memories:
            result.append(
                DecisionConfidence(
                    recommendation=memory.recommendation,
                    confidence=memory.confidence,
                    samples=memory.total,
                )
            )

        return sorted(
            result,
            key=lambda item: item.confidence,
            reverse=True,
        )