from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LearningSignal:
    experience: str
    improvement: float


class AdaptiveLearningEngine:

    def learn(
        self,
        experience: str,
        improvement: float,
    ) -> LearningSignal:

        if not experience.strip():
            raise ValueError(
                "experience must not be empty"
            )

        if not 0 <= improvement <= 1:
            raise ValueError(
                "improvement must be between 0 and 1"
            )

        return LearningSignal(
            experience=experience,
            improvement=improvement,
        )