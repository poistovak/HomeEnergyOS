from __future__ import annotations

from dataclasses import dataclass

from .decision_feedback import (
    DecisionFeedback,
)


@dataclass(frozen=True, slots=True)
class ConsolidatedDecisionMemory:
    recommendation: str
    total: int
    successful: int
    confidence: float


class DecisionMemoryConsolidator:

    def consolidate(
        self,
        feedback: list[DecisionFeedback],
    ) -> list[ConsolidatedDecisionMemory]:

        groups: dict[str, list[DecisionFeedback]] = {}

        for item in feedback:
            groups.setdefault(
                item.recommendation,
                [],
            ).append(item)

        result: list[ConsolidatedDecisionMemory] = []

        for recommendation, items in groups.items():

            successful = sum(
                1
                for item in items
                if item.success
            )

            confidence = (
                successful / len(items)
                if items
                else 0.0
            )

            result.append(
                ConsolidatedDecisionMemory(
                    recommendation=recommendation,
                    total=len(items),
                    successful=successful,
                    confidence=confidence,
                )
            )

        return result