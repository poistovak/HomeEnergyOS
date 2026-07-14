from heos.compiler.compiler import DecisionCompiler
from heos.compiler.execution_plan import ExecutionPlan
from heos.execution import ExecutionResult, ExecutionRuntime, ExecutionStatus
from heos.execution.drivers import DryRunExecutionDriver

class FailingDriver:
    def __init__(self, fail_at: int) -> None:
        self._index = 0
        self._fail_at = fail_at

    def execute(self, step):
        current = self._index
        self._index += 1
        if current == self._fail_at:
            return ExecutionResult(False, f"Rejected: {step.description}")
        return ExecutionResult(True, f"Executed: {step.description}")

def test_runtime_completes_compiled_charge_plan() -> None:
    plan = DecisionCompiler().compile("charge_ev_now")
    report = ExecutionRuntime(DryRunExecutionDriver()).run(plan)
    assert report.status is ExecutionStatus.COMPLETED
    assert report.completed_steps == len(plan.steps)
    assert len(report.journal) == len(plan.steps)

def test_runtime_stops_on_failure() -> None:
    plan = DecisionCompiler().compile("charge_ev_now")
    report = ExecutionRuntime(FailingDriver(2)).run(plan)
    assert report.status is ExecutionStatus.FAILED
    assert report.completed_steps == 2
    assert len(report.journal) == 3

def test_runtime_blocks_empty_plan() -> None:
    report = ExecutionRuntime(DryRunExecutionDriver()).run(
        ExecutionPlan(scenario_id="empty", steps=())
    )
    assert report.status is ExecutionStatus.BLOCKED

def test_dry_run_is_safe() -> None:
    plan = DecisionCompiler().compile("charge_ev_now")
    report = ExecutionRuntime(DryRunExecutionDriver()).run(plan)
    assert all(item.message.startswith("DRY-RUN:") for item in report.journal)
