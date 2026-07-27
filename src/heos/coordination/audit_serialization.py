from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .audit import CoordinationAuditRecord


def audit_record_to_dict(
    record: CoordinationAuditRecord,
) -> dict[str, Any]:
    return {
        "approval_resume": record.approval_resume,
        "autonomy_authorized": record.autonomy_authorized,
        "cycle_id": record.cycle_id,
        "digest": record.digest,
        "downgraded": record.downgraded,
        "effective_mode": record.effective_mode,
        "operator_approved": record.operator_approved,
        "previous_digest": record.previous_digest,
        "recorded_at": record.recorded_at.isoformat(),
        "release_id": record.release_id,
        "release_status": record.release_status,
        "requested_mode": record.requested_mode,
    }


def audit_record_from_dict(
    payload: Mapping[str, Any],
) -> CoordinationAuditRecord:
    return CoordinationAuditRecord(
        cycle_id=str(payload["cycle_id"]),
        requested_mode=str(payload["requested_mode"]),
        effective_mode=str(payload["effective_mode"]),
        downgraded=bool(payload["downgraded"]),
        operator_approved=bool(payload["operator_approved"]),
        autonomy_authorized=bool(payload["autonomy_authorized"]),
        release_status=str(payload["release_status"]),
        release_id=str(payload["release_id"]),
        approval_resume=bool(payload.get("approval_resume", False)),
        recorded_at=datetime.fromisoformat(str(payload["recorded_at"])),
        previous_digest=(
            None
            if payload.get("previous_digest") is None
            else str(payload["previous_digest"])
        ),
        digest=str(payload["digest"]),
    )


def dumps_audit_record(
    record: CoordinationAuditRecord,
) -> str:
    return json.dumps(
        audit_record_to_dict(record),
        sort_keys=True,
        separators=(",", ":"),
    )


def loads_audit_record(
    payload: str,
) -> CoordinationAuditRecord:
    decoded = json.loads(payload)

    if not isinstance(decoded, dict):
        raise TypeError(
            "coordination audit record must be a JSON object"
        )

    return audit_record_from_dict(decoded)