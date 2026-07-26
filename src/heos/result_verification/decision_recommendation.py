from __future__ import annotations

from dataclasses import dataclass

from .decision_query import (
    DecisionMemoryQuery,
    DecisionQuery,
)
from .decision_rank import (
    DecisionMemoryRanker,
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

        successful = sum(
            1
            for record in records
            if record.success
        )

        confidence = successful / len(records)

        return DecisionRecommendation(
            decision=best.record.decision,
            confidence=confidence,
        )