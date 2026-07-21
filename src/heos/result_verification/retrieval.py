from __future__ import annotations

from dataclasses import dataclass

from .learning import LearningRecord
from .learning_similarity import LearningSimilarity
from .memory import LearningMemory


@dataclass(frozen=True, slots=True)
class LearningRetrieval:
    memory: LearningMemory

    def find_similar(
        self,
        *,
        expected_value: float,
        similarity: LearningSimilarity,
    ) -> tuple[LearningRecord, ...]:
        return tuple(
            record
            for record in self.memory.all()
            if similarity.matches(
                record,
                expected_value,
            )
        )