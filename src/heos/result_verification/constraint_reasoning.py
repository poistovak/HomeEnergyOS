from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConstraintResult:
    allowed: bool
    reason: str


class ConstraintReasoningEngine:

    def evaluate(
        self,
        allowed: bool,
        reason: str,
    ) -> ConstraintResult:

        if not reason.strip():
            raise ValueError(
                "reason must not be empty"
            )

        return ConstraintResult(
            allowed=allowed,
            reason=reason,
        )