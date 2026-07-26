from __future__ import annotations

from dataclasses import dataclass

from .context_similarity import ContextSimilarityEngine
from .decision_context import DecisionContextMemory
from .decision_memory import DecisionMemory
from .decision_recommendation import DecisionRecommendation


@dataclass(frozen=True, slots=True)
class ContextAwareDecisionRecommender:
    context_memory: DecisionContextMemory
    decision_memory: DecisionMemory
    similarity_engine: ContextSimilarityEngine
    minimum_similarity: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_similarity <= 1.0:
            raise ValueError(
                "minimum_similarity must be between 0 and 1"
            )

    def recommend(
        self,
        context: dict[str, object],
    ) -> DecisionRecommendation | None:
        if not context:
            raise ValueError(
                "context must not be empty"
            )

        context_scores: dict[str, float] = {}

        for item in self.context_memory.all():
            similarity = self.similarity_engine.compare(
                item.context,
                context,
            ).score

            if similarity < self.minimum_similarity:
                continue

            previous = context_scores.get(
                item.decision,
                0.0,
            )

            context_scores[item.decision] = max(
                previous,
                similarity,
            )

        candidates: list[DecisionRecommendation] = []

        for decision, similarity in context_scores.items():
            records = [
                record
                for record in self.decision_memory.all()
                if record.decision == decision
            ]

            if not records:
                continue

            successful = sum(
                1
                for record in records
                if record.success
            )

            success_rate = successful / len(records)

            confidence = similarity * success_rate

            if confidence <= 0.0:
                continue

            candidates.append(
                DecisionRecommendation(
                    decision=decision,
                    confidence=confidence,
                )
            )

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda item: item.confidence,
        )