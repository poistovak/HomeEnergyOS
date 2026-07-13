"""Candidate decision model used by the HEOS Decision Engine."""

from __future__ import annotations

from dataclasses import dataclass

from .decision import Decision


@dataclass(frozen=True, slots=True)
class Candidate:
    """A decision proposal enriched with selection metadata."""

    decision: Decision
    brain_id: str
    priority: int
    utility: float = 0.0

    def __post_init__(self) -> None:
        if not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")
        if not -1.0 <= self.utility <= 1.0:
            raise ValueError("utility must be between -1.0 and 1.0")

    @property
    def score(self) -> float:
        """Deterministic score used to rank candidates."""
        confidence_score = self.decision.confidence * 100.0
        utility_score = self.utility * 20.0
        return self.priority + confidence_score + utility_score
