from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class CoordinationAuditRecord:
    """Immutable record of one coordination authorization decision."""

    cycle_id: str
    requested_mode: str
    effective_mode: str
    downgraded: bool
    operator_approved: bool
    autonomy_authorized: bool
    release_status: str
    release_id: str
    approval_resume: bool = False
    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if not self.cycle_id.strip():
            raise ValueError("cycle_id must not be empty")
        if not self.requested_mode.strip():
            raise ValueError("requested_mode must not be empty")
        if not self.effective_mode.strip():
            raise ValueError("effective_mode must not be empty")
        if not self.release_status.strip():
            raise ValueError("release_status must not be empty")
        if not self.release_id.strip():
            raise ValueError("release_id must not be empty")


@dataclass(slots=True)
class CoordinationAuditTrail:
    """Append-only audit trail for coordination authorization decisions."""

    _records: list[CoordinationAuditRecord] = field(default_factory=list)

    def append(
        self,
        record: CoordinationAuditRecord,
    ) -> CoordinationAuditRecord:
        self._records.append(record)
        return record

    def records(self) -> tuple[CoordinationAuditRecord, ...]:
        return tuple(self._records)

    def for_cycle(
        self,
        cycle_id: str,
    ) -> tuple[CoordinationAuditRecord, ...]:
        return tuple(
            record
            for record in self._records
            if record.cycle_id == cycle_id
        )