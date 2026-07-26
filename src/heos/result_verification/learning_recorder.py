from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .learning import LearningRecord
from .learning_bridge import LearningBridge
from .memory import LearningMemory
from .models import ResultExpectation, VerificationDecision


@dataclass(slots=True)
class LearningRecorder:
    memory: LearningMemory
    bridge: LearningBridge

    def __init__(
        self,
        memory: LearningMemory,
        bridge: LearningBridge | None = None,
    ) -> None:
        self.memory = memory
        self.bridge = bridge or LearningBridge()

    def record(
        self,
        *,
        prediction_id: str,
        expectation: ResultExpectation,
        decision: VerificationDecision,
        timestamp: datetime,
    ) -> LearningRecord | None:
        record = self.bridge.build_record(
            prediction_id=prediction_id,
            expectation=expectation,
            decision=decision,
            timestamp=timestamp,
        )

        if record is None:
            return None

        self.memory.add(record)

        return record