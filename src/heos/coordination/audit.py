from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256


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
    previous_digest: str | None = None
    digest: str = ""

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
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware")

    @staticmethod
    def canonical_payload(
        *,
        cycle_id: str,
        requested_mode: str,
        effective_mode: str,
        downgraded: bool,
        operator_approved: bool,
        autonomy_authorized: bool,
        release_status: str,
        release_id: str,
        approval_resume: bool,
        recorded_at: datetime,
        previous_digest: str | None,
    ) -> str:
        return json.dumps(
            {
                "approval_resume": approval_resume,
                "autonomy_authorized": autonomy_authorized,
                "cycle_id": cycle_id,
                "downgraded": downgraded,
                "effective_mode": effective_mode,
                "operator_approved": operator_approved,
                "previous_digest": previous_digest,
                "recorded_at": recorded_at.isoformat(),
                "release_id": release_id,
                "release_status": release_status,
                "requested_mode": requested_mode,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def issue(
        cls,
        *,
        cycle_id: str,
        requested_mode: str,
        effective_mode: str,
        downgraded: bool,
        operator_approved: bool,
        autonomy_authorized: bool,
        release_status: str,
        release_id: str,
        approval_resume: bool = False,
        recorded_at: datetime | None = None,
        previous_digest: str | None = None,
    ) -> CoordinationAuditRecord:
        timestamp = recorded_at or datetime.now(UTC)

        payload = cls.canonical_payload(
            cycle_id=cycle_id,
            requested_mode=requested_mode,
            effective_mode=effective_mode,
            downgraded=downgraded,
            operator_approved=operator_approved,
            autonomy_authorized=autonomy_authorized,
            release_status=release_status,
            release_id=release_id,
            approval_resume=approval_resume,
            recorded_at=timestamp,
            previous_digest=previous_digest,
        )

        return cls(
            cycle_id=cycle_id,
            requested_mode=requested_mode,
            effective_mode=effective_mode,
            downgraded=downgraded,
            operator_approved=operator_approved,
            autonomy_authorized=autonomy_authorized,
            release_status=release_status,
            release_id=release_id,
            approval_resume=approval_resume,
            recorded_at=timestamp,
            previous_digest=previous_digest,
            digest=sha256(payload.encode()).hexdigest(),
        )

    def verify(self) -> bool:
        payload = self.canonical_payload(
            cycle_id=self.cycle_id,
            requested_mode=self.requested_mode,
            effective_mode=self.effective_mode,
            downgraded=self.downgraded,
            operator_approved=self.operator_approved,
            autonomy_authorized=self.autonomy_authorized,
            release_status=self.release_status,
            release_id=self.release_id,
            approval_resume=self.approval_resume,
            recorded_at=self.recorded_at,
            previous_digest=self.previous_digest,
        )

        return sha256(payload.encode()).hexdigest() == self.digest


@dataclass(slots=True)
class CoordinationAuditTrail:
    """Append-only tamper-evident coordination audit trail."""

    _records: list[CoordinationAuditRecord] = field(default_factory=list)

    def append(
        self,
        record: CoordinationAuditRecord,
    ) -> CoordinationAuditRecord:
        if not record.verify():
            raise ValueError("invalid coordination audit record")

        expected = (
            self._records[-1].digest
            if self._records
            else None
        )

        if record.previous_digest != expected:
            raise ValueError("coordination audit chain mismatch")

        self._records.append(record)
        return record

    def issue_and_append(
        self,
        *,
        cycle_id: str,
        requested_mode: str,
        effective_mode: str,
        downgraded: bool,
        operator_approved: bool,
        autonomy_authorized: bool,
        release_status: str,
        release_id: str,
        approval_resume: bool = False,
        recorded_at: datetime | None = None,
    ) -> CoordinationAuditRecord:
        previous_digest = (
            self._records[-1].digest
            if self._records
            else None
        )

        record = CoordinationAuditRecord.issue(
            cycle_id=cycle_id,
            requested_mode=requested_mode,
            effective_mode=effective_mode,
            downgraded=downgraded,
            operator_approved=operator_approved,
            autonomy_authorized=autonomy_authorized,
            release_status=release_status,
            release_id=release_id,
            approval_resume=approval_resume,
            recorded_at=recorded_at,
            previous_digest=previous_digest,
        )

        return self.append(record)

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

    def verify_chain(self) -> bool:
        previous: str | None = None

        for record in self._records:
            if record.previous_digest != previous:
                return False

            if not record.verify():
                return False

            previous = record.digest

        return True