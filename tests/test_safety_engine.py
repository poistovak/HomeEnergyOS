from heos.compiler.compiler import DecisionCompiler
from heos.compiler.execution_plan import ExecutionPlan
from heos.compiler.execution_step import ExecutionStep, StepType
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


def kernel(health: KernelHealth) -> KernelSnapshot:
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


def charge_plan() -> ExecutionPlan:
    return DecisionCompiler().compile("charge_ev_now")


def test_safe_plan_is_allowed() -> None:
    report = SafetyEngine().evaluate(
        SafetyContext(
            plan=charge_plan(),
            kernel=kernel(KernelHealth.READY),
            projected_grid_import_w=2000,
            maximum_grid_import_w=8000,
        )
    )

    assert report.verdict is SafetyVerdict.ALLOW
    assert report.allowed is True
    assert report.reasons == ()


def test_manual_lock_denies_plan() -> None:
    report = SafetyEngine().evaluate(
        SafetyContext(
            plan=charge_plan(),
            kernel=kernel(KernelHealth.READY),
            manual_lock=True,
        )
    )

    assert report.verdict is SafetyVerdict.DENY
    assert any(
        "Manual execution lock" in reason
        for reason in report.reasons
    )


def test_blocked_kernel_denies_plan() -> None:
    report = SafetyEngine().evaluate(
        SafetyContext(
            plan=charge_plan(),
            kernel=kernel(KernelHealth.BLOCKED),
        )
    )

    assert report.verdict is SafetyVerdict.DENY


def test_degraded_kernel_retries_later() -> None:
    report = SafetyEngine().evaluate(
        SafetyContext(
            plan=charge_plan(),
            kernel=kernel(KernelHealth.DEGRADED),
        )
    )

    assert report.verdict is SafetyVerdict.RETRY_LATER


def test_grid_import_over_limit_denies_plan() -> None:
    report = SafetyEngine().evaluate(
        SafetyContext(
            plan=charge_plan(),
            kernel=kernel(KernelHealth.READY),
            projected_grid_import_w=9000,
            maximum_grid_import_w=8000,
        )
    )

    assert report.verdict is SafetyVerdict.DENY
    assert any(
        "exceeds limit" in reason
        for reason in report.reasons
    )


def test_write_without_verification_is_denied() -> None:
    unsafe_plan = ExecutionPlan(
        scenario_id="unsafe",
        steps=(
            ExecutionStep(
                step_type=StepType.SET_CURRENT,
                description="Set current to 16 A",
            ),
        ),
    )

    report = SafetyEngine().evaluate(
        SafetyContext(
            plan=unsafe_plan,
            kernel=kernel(KernelHealth.READY),
        )
    )

    assert report.verdict is SafetyVerdict.DENY
    assert any(
        "without a following verification" in reason
        for reason in report.reasons
    )


def test_deny_has_priority_over_retry_later() -> None:
    report = SafetyEngine().evaluate(
        SafetyContext(
            plan=charge_plan(),
            kernel=kernel(KernelHealth.DEGRADED),
            manual_lock=True,
        )
    )

    assert report.verdict is SafetyVerdict.DENY
