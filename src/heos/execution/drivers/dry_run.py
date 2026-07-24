from heos.compiler.execution_step import ExecutionStep

from ..driver import ExecutionResult


class DryRunExecutionDriver:
    def execute(self, step: ExecutionStep) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            message=f"DRY-RUN: {step.description}",
        )
