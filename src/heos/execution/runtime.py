from __future__ import annotations

from heos.compiler.execution_plan import ExecutionPlan

from .driver import ExecutionDriver
from .models import ExecutionJournalEntry, ExecutionStatus, RuntimeReport


class ExecutionRuntime:
    def __init__(self, driver: ExecutionDriver) -> None:
        self._driver = driver

    def run(self, plan: ExecutionPlan) -> RuntimeReport:
        journal: list[ExecutionJournalEntry] = []

        if not plan.steps:
            return RuntimeReport(
                scenario_id=plan.scenario_id,
                status=ExecutionStatus.BLOCKED,
                completed_steps=0,
                total_steps=0,
                journal=(),
                failure_reason="Execution plan contains no steps.",
            )

        for index, step in enumerate(plan.steps):
            result = self._driver.execute(step)
            journal.append(
                ExecutionJournalEntry(
                    step_index=index,
                    step_type=step.step_type.value,
                    description=step.description,
                    success=result.success,
                    message=result.message,
                )
            )
            if not result.success:
                return RuntimeReport(
                    scenario_id=plan.scenario_id,
                    status=ExecutionStatus.FAILED,
                    completed_steps=index,
                    total_steps=len(plan.steps),
                    journal=tuple(journal),
                    failure_reason=result.message or f"Step {index} failed.",
                )

        return RuntimeReport(
            scenario_id=plan.scenario_id,
            status=ExecutionStatus.COMPLETED,
            completed_steps=len(plan.steps),
            total_steps=len(plan.steps),
            journal=tuple(journal),
        )
