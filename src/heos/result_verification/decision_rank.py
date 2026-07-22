from __future__ import annotations

from dataclasses import dataclass

from .decision_memory import DecisionMemoryRecord


@dataclass(frozen=True, slots=True)
class DecisionRank:
    record: DecisionMemoryRecord
    score: float


class DecisionMemoryRanker:

    def rank(
        self,
        records: list[DecisionMemoryRecord],
    ) -> list[DecisionRank]:

        ranked: list[DecisionRank] = []

        for record in records:

            score = 0.0

            if record.success:
                score += 10.0

            if hasattr(record, "expected_value"):
                score += 1.0

            ranked.append(
                DecisionRank(
                    record=record,
                    score=score,
                )
            )

        return sorted(
            ranked,
            key=lambda item: item.score,
            reverse=True,
        )