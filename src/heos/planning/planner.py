"""First deterministic HEOS Future Scenario Planner."""

from __future__ import annotations

from dataclasses import dataclass

from heos.kernel import KernelHealth, KernelSnapshot

from .goals import GoalKind, GoalSet
from .models import (
    FutureScenario,
    PlannedAction,
    ScenarioMetrics,
)


@dataclass(frozen=True, slots=True)
class PlannerPolicy:
    minimum_ev_charge_power_w: float = 1380.0
    maximum_ev_charge_power_w: float = 3680.0
    planning_horizon_hours: float = 0.25

    def __post_init__(self) -> None:
        if self.minimum_ev_charge_power_w <= 0:
            raise ValueError(
                "minimum_ev_charge_power_w must be positive"
            )
        if (
            self.maximum_ev_charge_power_w
            < self.minimum_ev_charge_power_w
        ):
            raise ValueError(
                "maximum_ev_charge_power_w must be >= minimum"
            )
        if self.planning_horizon_hours <= 0:
            raise ValueError(
                "planning_horizon_hours must be positive"
            )


class FutureScenarioPlanner:
    """Generate three explainable futures from one KernelSnapshot."""

    def __init__(
        self,
        policy: PlannerPolicy | None = None,
    ) -> None:
        self._policy = policy or PlannerPolicy()

    def generate(
        self,
        snapshot: KernelSnapshot,
        goals: GoalSet,
        *,
        ev_resource_id: str = "storage.ev",
    ) -> tuple[FutureScenario, ...]:
        if snapshot.health is KernelHealth.BLOCKED:
            return (self._blocked_scenario(snapshot),)

        balance = snapshot.balance
        surplus_w = max(balance.net_w, 0.0)

        scenarios = [
            self._wait_scenario(snapshot, goals),
            self._export_scenario(snapshot, goals, surplus_w),
        ]

        if surplus_w >= self._policy.minimum_ev_charge_power_w:
            scenarios.append(
                self._charge_ev_scenario(
                    snapshot,
                    goals,
                    surplus_w,
                    ev_resource_id=ev_resource_id,
                )
            )

        return tuple(
            sorted(
                scenarios,
                key=lambda scenario: scenario.score,
                reverse=True,
            )
        )

    def _charge_ev_scenario(
        self,
        snapshot: KernelSnapshot,
        goals: GoalSet,
        surplus_w: float,
        *,
        ev_resource_id: str,
    ) -> FutureScenario:
        charge_power_w = min(
            surplus_w,
            self._policy.maximum_ev_charge_power_w,
        )
        energy_kwh = (
            charge_power_w
            * self._policy.planning_horizon_hours
            / 1000.0
        )

        self_consumption_gain = min(
            100.0,
            75.0 + (charge_power_w / 100.0),
        )

        score = (
            30.0
            + goals.weight_for(GoalKind.PREPARE_EV) * 35.0
            + goals.weight_for(
                GoalKind.MAXIMIZE_SELF_CONSUMPTION
            ) * 25.0
            + goals.weight_for(GoalKind.PROTECT_GRID) * 10.0
        )

        return FutureScenario(
            scenario_id="charge_ev_now",
            title="Charge EV from available surplus",
            actions=(
                PlannedAction(
                    action_id="increase_ev_energy",
                    target_resource_id=ev_resource_id,
                    parameters={
                        "power_w": round(charge_power_w, 2),
                    },
                    reason="Use current household energy surplus.",
                ),
            ),
            metrics=ScenarioMetrics(
                expected_grid_import_kwh=0.0,
                expected_grid_export_kwh=max(
                    (surplus_w - charge_power_w)
                    * self._policy.planning_horizon_hours
                    / 1000.0,
                    0.0,
                ),
                expected_self_consumption_percent=(
                    self_consumption_gain
                ),
                expected_ev_energy_kwh=energy_kwh,
                confidence=0.94,
            ),
            score=score,
            reasons=(
                f"Available surplus is {surplus_w:.0f} W.",
                f"EV can absorb {charge_power_w:.0f} W.",
                "Scenario supports EV readiness and self-consumption.",
            ),
        )

    def _export_scenario(
        self,
        snapshot: KernelSnapshot,
        goals: GoalSet,
        surplus_w: float,
    ) -> FutureScenario:
        export_kwh = (
            surplus_w
            * self._policy.planning_horizon_hours
            / 1000.0
        )

        score = (
            20.0
            + goals.weight_for(GoalKind.MINIMIZE_COST) * 15.0
            - goals.weight_for(
                GoalKind.MAXIMIZE_SELF_CONSUMPTION
            ) * 10.0
        )

        return FutureScenario(
            scenario_id="export_surplus",
            title="Export available surplus",
            actions=(
                PlannedAction(
                    action_id="export_energy",
                    target_resource_id="grid.main",
                    parameters={
                        "power_w": round(surplus_w, 2),
                    },
                    reason="No higher-priority local use selected.",
                ),
            ) if surplus_w > 0 else (),
            metrics=ScenarioMetrics(
                expected_grid_export_kwh=export_kwh,
                expected_self_consumption_percent=60.0,
                confidence=0.98,
            ),
            score=score,
            reasons=(
                f"Projected export is {export_kwh:.3f} kWh.",
                "Export remains available as a safe fallback.",
            ),
        )

    def _wait_scenario(
        self,
        snapshot: KernelSnapshot,
        goals: GoalSet,
    ) -> FutureScenario:
        score = (
            10.0
            + goals.weight_for(GoalKind.PRESERVE_STORAGE) * 10.0
        )

        return FutureScenario(
            scenario_id="wait",
            title="Keep current operating state",
            actions=(),
            metrics=ScenarioMetrics(
                expected_grid_import_kwh=max(
                    snapshot.balance.net_w,
                    0.0,
                )
                * self._policy.planning_horizon_hours
                / 1000.0,
                expected_grid_export_kwh=max(
                    -snapshot.balance.net_w,
                    0.0,
                )
                * self._policy.planning_horizon_hours
                / 1000.0,
                expected_self_consumption_percent=50.0,
                confidence=0.99,
            ),
            score=score,
            reasons=(
                "No change is always retained as a fallback future.",
            ),
        )

    @staticmethod
    def _blocked_scenario(
        snapshot: KernelSnapshot,
    ) -> FutureScenario:
        return FutureScenario(
            scenario_id="blocked",
            title="Planning blocked by kernel health",
            actions=(),
            metrics=ScenarioMetrics(confidence=1.0),
            score=100.0,
            reasons=tuple(
                issue.message for issue in snapshot.issues
            ) or ("Kernel is blocked.",),
        )
