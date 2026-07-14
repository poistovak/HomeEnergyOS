from __future__ import annotations

from collections.abc import Iterable

from heos.resources import (
    EnergyResource,
    ResourceGraph,
    ResourceHealth,
    ResourceKind,
    ResourceState,
)

from .models import (
    EnergyBalance,
    KernelHealth,
    KernelSnapshot,
    TopologyIssue,
)


class EnergyKernel:
    """Central coordinator of the HEOS energy model.

    The kernel understands resources, states, topology and balance.
    It does not know vendors and it never calls device APIs directly.
    """

    def __init__(self, graph: ResourceGraph | None = None) -> None:
        self.graph = graph or ResourceGraph()

    def register(self, resource: EnergyResource) -> None:
        self.graph.add_resource(resource)

    def observe(self, state: ResourceState) -> None:
        self.graph.registry.get(state.resource_id).update_state(state)

    def observe_many(self, states: Iterable[ResourceState]) -> None:
        for state in states:
            self.observe(state)

    def snapshot(self) -> KernelSnapshot:
        issues = self.validate_topology()
        balance = self.calculate_balance()

        if any(issue.code == "FAILED_RESOURCE" for issue in issues):
            health = KernelHealth.BLOCKED
        elif issues:
            health = KernelHealth.DEGRADED
        else:
            health = KernelHealth.READY

        return KernelSnapshot(
            health=health,
            balance=balance,
            resource_count=len(self.graph.registry.all),
            flow_count=len(self.graph.flows),
            issues=issues,
        )

    def calculate_balance(self) -> EnergyBalance:
        production = 0.0
        consumption = 0.0
        storage_charge = 0.0
        storage_discharge = 0.0
        grid_import = 0.0
        grid_export = 0.0

        for resource in self.graph.registry.all:
            state = resource.state
            if state is None:
                continue

            power = self._power_w(state)

            if resource.kind is ResourceKind.PRODUCER:
                production += max(power, 0.0)
            elif resource.kind is ResourceKind.CONSUMER:
                consumption += max(power, 0.0)
            elif resource.kind is ResourceKind.STORAGE:
                if power >= 0:
                    storage_discharge += power
                else:
                    storage_charge += abs(power)
            elif resource.kind is ResourceKind.GRID:
                if power >= 0:
                    grid_import += power
                else:
                    grid_export += abs(power)

        return EnergyBalance(
            production_w=production,
            consumption_w=consumption,
            storage_charge_w=storage_charge,
            storage_discharge_w=storage_discharge,
            grid_import_w=grid_import,
            grid_export_w=grid_export,
        )

    def validate_topology(self) -> tuple[TopologyIssue, ...]:
        issues: list[TopologyIssue] = []

        for resource in self.graph.registry.all:
            state = resource.state

            if state is None:
                issues.append(
                    TopologyIssue(
                        code="MISSING_STATE",
                        message="Resource has no observed state.",
                        resource_id=resource.resource_id,
                    )
                )
                continue

            if state.health is ResourceHealth.FAILED:
                issues.append(
                    TopologyIssue(
                        code="FAILED_RESOURCE",
                        message="Resource reports failed health.",
                        resource_id=resource.resource_id,
                    )
                )
            elif state.health in {
                ResourceHealth.OFFLINE,
                ResourceHealth.UNKNOWN,
                ResourceHealth.DEGRADED,
            }:
                issues.append(
                    TopologyIssue(
                        code="UNHEALTHY_RESOURCE",
                        message=f"Resource health is {state.health.value}.",
                        resource_id=resource.resource_id,
                    )
                )

        return tuple(issues)

    def can_route(self, source_id: str, destination_id: str) -> bool:
        return self.graph.has_path(source_id, destination_id)

    @staticmethod
    def _power_w(state: ResourceState) -> float:
        value = getattr(state, "power_w", None)
        if value is None:
            value = state.attributes.get("power_w", 0.0)

        try:
            return float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid power_w for resource {state.resource_id!r}"
            ) from error
