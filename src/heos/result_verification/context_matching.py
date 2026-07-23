from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextMatch:
    decision: str
    matches: int


class ContextMatcher:

    def match(
        self,
        decision: str,
        history: list[dict[str, object]],
        context: dict[str, object],
    ) -> ContextMatch:

        if not decision.strip():
            raise ValueError(
                "decision must not be empty"
            )

        matches = 0

        for item in history:
            if item == context:
                matches += 1

        return ContextMatch(
            decision=decision,
            matches=matches,
        )