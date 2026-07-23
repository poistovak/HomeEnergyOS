from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankedExperience:
    experience: str
    score: float


class ExperienceRankingEngine:

    def rank(
        self,
        experiences: list[tuple[str, float]],
    ) -> list[RankedExperience]:

        ranked = sorted(
            experiences,
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            RankedExperience(
                experience=item[0],
                score=item[1],
            )
            for item in ranked
        ]