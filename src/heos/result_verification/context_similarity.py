from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextSimilarity:
    score: float


class ContextSimilarityEngine:

    def compare(
        self,
        first: dict[str, object],
        second: dict[str, object],
    ) -> ContextSimilarity:

        if not first:
            raise ValueError(
                "first context must not be empty"
            )

        if not second:
            raise ValueError(
                "second context must not be empty"
            )

        keys = set(first.keys()) & set(second.keys())

        if not keys:
            return ContextSimilarity(
                score=0.0
            )

        matches = sum(
            1
            for key in keys
            if first[key] == second[key]
        )

        score = round(
            matches / len(keys),
            10,
        )

        return ContextSimilarity(
            score=score
        )