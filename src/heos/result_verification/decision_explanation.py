from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionExplanation:
    decision: str
    reasons: list[str]


class DecisionExplanationEngine:

    def explain(
        self,
        decision: str,
        reasons: list[str],
    ) -> DecisionExplanation:

        if not decision.strip():
            raise ValueError(
                "decision must not be empty"
            )

        if not reasons:
            raise ValueError(
                "reasons must not be empty"
            )

        return DecisionExplanation(
            decision=decision,
            reasons=list(reasons),
        )