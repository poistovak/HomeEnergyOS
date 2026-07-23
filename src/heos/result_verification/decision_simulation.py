from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationResult:
    scenario: str
    expected_value: float


class DecisionSimulationEngine:

    def simulate(
        self,
        scenarios: list[tuple[str, float]],
    ) -> list[SimulationResult]:

        if not scenarios:
            raise ValueError(
                "scenarios must not be empty"
            )

        return [
            SimulationResult(
                scenario=name,
                expected_value=value,
            )
            for name, value in scenarios
        ]