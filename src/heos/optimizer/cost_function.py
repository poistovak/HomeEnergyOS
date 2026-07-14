"""Cost function primitives for HEOS optimization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CostBreakdown:
    """Normalized optimization costs.

    Lower values are better.
    """

    energy_cost: float = 0.0
    grid_import: float = 0.0
    carbon_emissions: float = 0.0
    battery_degradation: float = 0.0
    comfort_penalty: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.energy_cost
            + self.grid_import
            + self.carbon_emissions
            + self.battery_degradation
            + self.comfort_penalty
        )


class CostFunction:
    """Calculate a deterministic score for an action plan."""

    def evaluate(self, costs: CostBreakdown) -> float:
        return costs.total