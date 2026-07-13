"""HEOS brain orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from .brain import Brain
from .candidate import Candidate
from .decision_engine import DecisionEngine, SelectionResult
from .state import HouseState


@dataclass(frozen=True, slots=True)
class BrainRegistration:
    brain: Brain
    priority: int
    utility: float = 0.0


class BrainOrchestrator:
    """Run registered brains and select one explainable decision."""

    def __init__(
        self,
        registrations: tuple[BrainRegistration, ...],
        *,
        minimum_confidence: float = 0.60,
    ) -> None:
        self._registrations = registrations
        self._engine = DecisionEngine(
            minimum_confidence=minimum_confidence
        )

    def evaluate(self, state: HouseState) -> SelectionResult:
        candidates: list[Candidate] = []

        for registration in self._registrations:
            for decision in registration.brain.propose(state):
                candidates.append(
                    Candidate(
                        decision=decision,
                        brain_id=registration.brain.brain_id,
                        priority=registration.priority,
                        utility=registration.utility,
                    )
                )

        return self._engine.select(tuple(candidates))
