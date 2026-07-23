from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    actual: str
    alternative: str
    difference: float


class CounterfactualReasoningEngine:

    def compare(
        self,
        actual: str,
        alternative: str,
        actual_value: float,
        alternative_value: float,
    ) -> CounterfactualResult:

        if not actual.strip():
            raise ValueError(
                "actual must not be empty"
            )

        if not alternative.strip():
            raise ValueError(
                "alternative must not be empty"
            )

        return CounterfactualResult(
            actual=actual,
            alternative=alternative,
            difference=round(
                actual_value - alternative_value,
                10,
            ),
        )