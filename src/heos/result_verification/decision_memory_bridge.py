from __future__ import annotations

from dataclasses import dataclass

from .decision_memory import DecisionMemoryRecord
from .learning import LearningRecord


@dataclass(frozen=True, slots=True)
class DecisionMemoryBridge:
    def build_record(
        self,
        *,
        learning: LearningRecord,
        decision: str,
        outcome: str,
    ) -> DecisionMemoryRecord:
        if not decision.strip():
            raise ValueError("decision must not be empty")

        if not outcome.strip():
            raise ValueError("outcome must not be empty")

        return DecisionMemoryRecord(
            command_id=learning.command_id,
            decision=decision,
            outcome=outcome,
            expected_value=learning.expected_value,
            actual_value=learning.actual_value,
            success=learning.success,
            created_at=learning.timestamp,
        )