from datetime import UTC, datetime

from heos.execution import ExecutionJournalEntry, ExecutionStatus as RuntimeExecutionStatus
from heos.execution import RuntimeReport
from heos.feedback import ActionRecord, ExecutionStatus
from heos.feedback.runtime_bridge import (
    actions_from_runtime_report,
    execution_status_from_runtime_report,
)


def runtime_report(status: RuntimeExecutionStatus) -> RuntimeReport:
    return RuntimeReport(
        scenario_id="charge_ev_now",
        status=status,
        completed_steps=1,
        total_steps=1,
        journal=(
            ExecutionJournalEntry(
                step_index=0,
                step_type="set_power",
                description="Set EV charging power",
                success=True,
                message="DRY-RUN: accepted",
                created_at=datetime(2026, 7, 15, 10, tzinfo=UTC),
            ),
        ),
        failure_reason=None,
    )


def test_execution_status_from_runtime_report_maps_public_runtime_enum() -> None:
    report = runtime_report(RuntimeExecutionStatus.COMPLETED)
    assert execution_status_from_runtime_report(report) is ExecutionStatus.COMPLETED


def test_actions_from_runtime_report_maps_successful_journal_entries() -> None:
    report = runtime_report(RuntimeExecutionStatus.COMPLETED)
    assert actions_from_runtime_report(report) == (
        ActionRecord(
            resource_id="runtime.step.0",
            action="set_power",
            metadata={
                "description": "Set EV charging power",
                "message": "DRY-RUN: accepted",
                "success": "true",
            },
        ),
    )


def test_actions_from_runtime_report_ignores_failed_entries() -> None:
    report = RuntimeReport(
        scenario_id="charge_ev_now",
        status=RuntimeExecutionStatus.FAILED,
        completed_steps=0,
        total_steps=1,
        journal=(
            ExecutionJournalEntry(
                step_index=0,
                step_type="set_power",
                description="Set EV charging power",
                success=False,
                message="Rejected",
                created_at=datetime(2026, 7, 15, 10, tzinfo=UTC),
            ),
        ),
        failure_reason="Rejected",
    )
    assert actions_from_runtime_report(report) == ()
