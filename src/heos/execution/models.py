from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

class ExecutionStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass(frozen=True, slots=True)
class ExecutionJournalEntry:
    step_index: int
    step_type: str
    description: str
    success: bool
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass(frozen=True, slots=True)
class RuntimeReport:
    scenario_id: str
    status: ExecutionStatus
    completed_steps: int
    total_steps: int
    journal: tuple[ExecutionJournalEntry, ...]
    failure_reason: str | None = None

    @property
    def successful(self) -> bool:
        return self.status is ExecutionStatus.COMPLETED
