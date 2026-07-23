from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExperienceMatch:
    experience: str
    score: float


class ExperienceRetrievalEngine:

    def retrieve(
        self,
        experiences: list[tuple[str, float]],
    ) -> ExperienceMatch | None:

        if not experiences:
            return None

        best = max(
            experiences,
            key=lambda item: item[1],
        )

        return ExperienceMatch(
            experience=best[0],
            score=best[1],
        )