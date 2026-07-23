from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlanOption:
    name: str
    score: float


class MultiOptionPlanner:

    def plan(
        self,
        options: list[tuple[str, float]],
    ) -> list[PlanOption]:

        if not options:
            raise ValueError(
                "options must not be empty"
            )

        ranked = sorted(
            options,
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            PlanOption(
                name=name,
                score=score,
            )
            for name, score in ranked
        ]