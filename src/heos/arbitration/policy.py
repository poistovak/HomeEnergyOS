"""Arbitration policy contracts and default deterministic policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import ArbitrationCandidate


class ArbitrationPolicy(Protocol):
    def sort_key(
        self,
        candidate: ArbitrationCandidate,
    ) -> tuple[float, ...] | tuple[float, ..., str]:
        """Return deterministic descending-order ranking key."""


@dataclass(frozen=True, slots=True)
class DefaultArbitrationPolicy:
    """Rank by validity, policy priority, score, confidence and ID.

    Scenario ID is the final deterministic tie-breaker.
    """

    def sort_key(
        self,
        candidate: ArbitrationCandidate,
    ) -> tuple[float, float, float, float, str]:
        scenario = candidate.scenario

        return (
            1.0 if candidate.valid else 0.0,
            float(candidate.policy_priority),
            float(scenario.score),
            float(scenario.metrics.confidence),
            self._reverse_text_key(scenario.scenario_id),
        )

    @staticmethod
    def _reverse_text_key(value: str) -> str:
        """Create an inverse key so ascending IDs win in reverse sort."""
        return "".join(
            chr(0x10FFFF - ord(character))
            for character in value
        )
