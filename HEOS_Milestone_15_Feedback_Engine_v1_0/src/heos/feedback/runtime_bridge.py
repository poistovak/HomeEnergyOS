from __future__ import annotations

from datetime import datetime
from typing import Mapping

from .models import ActionRecord, DecisionRecord, ExecutionStatus, OutcomeRecord


def _status_from_runtime(value: object) -> ExecutionStatus:
    raw = getattr(value, "value", value)
    normalized = str(raw).strip().lower()
    try:
        return ExecutionStatus(normalized)
    except ValueError:
        return ExecutionStatus.UNKNOWN


def outcome_from_runtime_report(
    decision: DecisionRecord,
    report: object,
    *,
    record_id: str,
    observed_at: datetime,
    actual_state: Mapping[str, float],
) -> OutcomeRecord:
    journal = tuple(getattr(report, "journal", ()))
    executed_actions = tuple(
        ActionRecord(
            resource_id=f"runtime.step.{index}",
            action=str(getattr(item, "step_type", "unknown")),
            metadata={
                "description": str(getattr(item, "description", "")),
                "message": str(getattr(item, "message", "")),
                "success": str(bool(getattr(item, "success", False))).lower(),
            },
        )
        for index, item in enumerate(journal)
        if bool(getattr(item, "success", False))
    )
    status = _status_from_runtime(getattr(report, "status", "unknown"))
    failure_reason = getattr(report, "failure_reason", None)
    notes = (str(failure_reason),) if failure_reason else ()
    return OutcomeRecord(
        record_id=record_id,
        decision_record_id=decision.record_id,
        observed_at=observed_at,
        window_start=decision.effective_from,
        window_end=decision.effective_until,
        actual_state=actual_state,
        executed_actions=executed_actions,
        status=status,
        constraints_satisfied=status not in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED),
        violations=notes,
        notes=notes,
    )
