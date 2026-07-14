from heos.kernel import (
    EnergyBalance,
    KernelHealth,
    KernelSnapshot,
    TopologyIssue,
)
from heos.planning import (
    FutureScenarioPlanner,
    Goal,
    GoalKind,
    GoalSet,
)


def goals() -> GoalSet:
    return GoalSet(
        goals=(
            Goal(GoalKind.PREPARE_EV, 1.0),
            Goal(GoalKind.MAXIMIZE_SELF_CONSUMPTION, 0.8),
            Goal(GoalKind.PROTECT_GRID, 0.7),
        )
    )


def test_planner_generates_three_futures_with_surplus() -> None:
    snapshot = KernelSnapshot(
        health=KernelHealth.READY,
        balance=EnergyBalance(
            production_w=5000,
            consumption_w=1500,
            storage_charge_w=0,
            storage_discharge_w=0,
            grid_import_w=0,
            grid_export_w=0,
        ),
        resource_count=4,
        flow_count=3,
    )

    scenarios = FutureScenarioPlanner().generate(
        snapshot,
        goals(),
    )

    assert len(scenarios) == 3
    assert scenarios[0].scenario_id == "charge_ev_now"
    assert scenarios[0].metrics.expected_ev_energy_kwh > 0


def test_planner_keeps_wait_as_fallback() -> None:
    snapshot = KernelSnapshot(
        health=KernelHealth.READY,
        balance=EnergyBalance(
            production_w=1000,
            consumption_w=1000,
            storage_charge_w=0,
            storage_discharge_w=0,
            grid_import_w=0,
            grid_export_w=0,
        ),
        resource_count=2,
        flow_count=1,
    )

    scenarios = FutureScenarioPlanner().generate(
        snapshot,
        goals(),
    )

    assert any(
        scenario.scenario_id == "wait"
        for scenario in scenarios
    )


def test_blocked_kernel_produces_only_blocked_future() -> None:
    snapshot = KernelSnapshot(
        health=KernelHealth.BLOCKED,
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
        issues=(
            TopologyIssue(
                code="FAILED_RESOURCE",
                message="Solar resource failed.",
                resource_id="producer.solar",
            ),
        ),
    )

    scenarios = FutureScenarioPlanner().generate(
        snapshot,
        goals(),
    )

    assert len(scenarios) == 1
    assert scenarios[0].scenario_id == "blocked"
    assert scenarios[0].executable is False


def test_goal_weights_change_scenario_ranking() -> None:
    snapshot = KernelSnapshot(
        health=KernelHealth.READY,
        balance=EnergyBalance(
            production_w=5000,
            consumption_w=1500,
            storage_charge_w=0,
            storage_discharge_w=0,
            grid_import_w=0,
            grid_export_w=0,
        ),
        resource_count=4,
        flow_count=3,
    )
    export_goals = GoalSet(
        goals=(
            Goal(GoalKind.MINIMIZE_COST, 4.0),
            Goal(GoalKind.MAXIMIZE_SELF_CONSUMPTION, 0.0),
            Goal(GoalKind.PREPARE_EV, 0.0),
        )
    )

    scenarios = FutureScenarioPlanner().generate(
        snapshot,
        export_goals,
    )

    assert scenarios[0].scenario_id == "export_surplus"
