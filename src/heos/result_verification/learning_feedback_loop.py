from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeedbackResult:
    improvement: float
    accepted: bool


class LearningFeedbackLoopEngine:

    def evaluate(
        self,
        improvement: float,
    ) -> FeedbackResult:

        if not -1 <= improvement <= 1:
            raise ValueError(
                "improvement must be between -1 and 1"
            )

        return FeedbackResult(
            improvement=improvement,
            accepted=improvement > 0,
        )