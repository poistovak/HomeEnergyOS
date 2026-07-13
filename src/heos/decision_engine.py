"""HEOS Decision Engine.

The engine ranks candidate decisions deterministically.
It does not execute actions and does not bypass the Safety Layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from .candidate import Candidate
from .decision import Decision


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """Result of a Decision Engine evaluation."""

    selected: Candidate | None
    considered: tuple[Candidate, ...]
    rejected: tuple[Candidate, ...]

    @property
    def decision(self) -> Decision | None:
        return None if self.selected is None else self.selected.decision


class DecisionEngine:
    """Select the best non-expired candidate using explicit rules."""

    def __init__(self, *, minimum_confidence: float = 0.60) -> None:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0.0 and 1.0")
        self._minimum_confidence = minimum_confidence

    def select(self, candidates: tuple[Candidate, ...]) -> SelectionResult:
        """Select one candidate and preserve a full audit trail."""
        valid: list[Candidate] = []
        rejected: list[Candidate] = []

        for candidate in candidates:
            decision = candidate.decision
            if decision.is_expired():
                rejected.append(candidate)
                continue
            if decision.confidence < self._minimum_confidence:
                rejected.append(candidate)
                continue
            valid.append(candidate)

        ranked = sorted(
            valid,
            key=lambda item: (
                item.score,
                item.priority,
                item.decision.confidence,
                item.brain_id,
            ),
            reverse=True,
        )

        selected = ranked[0] if ranked else None
        return SelectionResult(
            selected=selected,
            considered=tuple(ranked),
            rejected=tuple(rejected),
        )
