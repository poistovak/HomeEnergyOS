from __future__ import annotations

from dataclasses import dataclass

from .decision_rank import (
    DecisionMemoryRanker,
)

from .decision_query import (
    DecisionMemoryQuery,
    DecisionQuery,
)


@dataclass(frozen=True, slots=True)
class DecisionRecommendation:
    decision: str
    confidence: float


class DecisionMemoryRecommender:

    def __init__(
        self,
        query: DecisionMemoryQuery,
        ranker: DecisionMemoryRanker,
    ) -> None:
        self.query = query
        self.ranker = ranker

    def recommend(
        self,
        request: DecisionQuery,
    ) -> DecisionRecommendation | None:

        records = self.query.search(request)

        if not records:
            return None

        ranked = self.ranker.rank(records)

        best = ranked[0]

        return DecisionRecommendation(
            decision=best.record.decision,
            confidence=best.score,
        )