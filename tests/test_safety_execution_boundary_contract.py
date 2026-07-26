from heos.compiler import DecisionCompiler
from heos.execution import (
    ExecutionResult,
    ExecutionRuntime,
    ExecutionStatus,
)
from heos.execution.safety_gate import (
    SafetyExecutionGate,
)
from heos.kernel import (
    EnergyBalance,
    KernelHealth,
    KernelSnapshot,
)
from heos.safety import (
    SafetyContext,
    SafetyEngine,
    SafetyVerdict,
)


class CountingDriver:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, step):
        self.calls += 1
        return ExecutionResult(
            success=True,
            message=f"Executed: {step.description}",
        )


def kernel(
    health: KernelHealth,
) -> KernelSnapshot:
    return KernelSnapshot(
        health=health,
        balance=EnergyBalance(
            production_w=0,
            consumption_w=0,
            storage_charge_w=0,
            storage_discharge_w=0,
            grid_import_w=0,
            grid_export_w=0,
        ),
        resource_count=1,
        flow_count=0,
    )


def charge_context(
    *,
    health: KernelHealth = KernelHealth.READY,
    manual_lock: bool = False,
) -> SafetyContext:
    return SafetyContext(
        plan=DecisionCompiler().compile(
            "charge_ev_now"
        ),
        kernel=kernel(health),
        manual_lock=manual_lock,
        projected_grid_import_w=2000,
        maximum_grid_import_w=8000,
    )


def test_allowed_plan_reaches_execution_runtime():
    driver = CountingDriver()

    gate = SafetyExecutionGate(
        safety_engine=SafetyEngine(),
        runtime=ExecutionRuntime(driver),
    )

    result = gate.run(
        charge_context()
    )

    assert result.safety.verdict is SafetyVerdict.ALLOW
    assert result.executed is True
    assert result.runtime is not None
    assert result.runtime.status is ExecutionStatus.COMPLETED
    assert driver.calls == 5


def test_manual_lock_prevents_any_driver_call():
    driver = CountingDriver()

    gate = SafetyExecutionGate(
        safety_engine=SafetyEngine(),
        runtime=ExecutionRuntime(driver),
    )

    result = gate.run(
        charge_context(
            manual_lock=True,
        )
    )

    assert result.safety.verdict is SafetyVerdict.DENY
    assert result.executed is False
    assert result.runtime is None
    assert driver.calls == 0


def test_degraded_kernel_does_not_execute():
    driver = CountingDriver()

    gate = SafetyExecutionGate(
        safety_engine=SafetyEngine(),
        runtime=ExecutionRuntime(driver),
    )

    result = gate.run(
        charge_context(
            health=KernelHealth.DEGRADED,
        )
    )

    assert result.safety.verdict is SafetyVerdict.RETRY_LATER
    assert result.executed is False
    assert result.runtime is None
    assert driver.calls == 0


def test_blocked_kernel_does_not_execute():
    driver = CountingDriver()

    gate = SafetyExecutionGate(
        safety_engine=SafetyEngine(),
        runtime=ExecutionRuntime(driver),
    )

    result = gate.run(
        charge_context(
            health=KernelHealth.BLOCKED,
        )
    )

    assert result.safety.verdict is SafetyVerdict.DENY
    assert result.executed is False
    assert driver.calls == 0