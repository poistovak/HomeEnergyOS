from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CausalRelationship:
    cause: str
    effect: str
    strength: float


class CausalRelationshipEngine:

    def create(
        self,
        cause: str,
        effect: str,
        strength: float,
    ) -> CausalRelationship:

        if not cause.strip():
            raise ValueError(
                "cause must not be empty"
            )

        if not effect.strip():
            raise ValueError(
                "effect must not be empty"
            )

        if not 0 <= strength <= 1:
            raise ValueError(
                "strength must be between 0 and 1"
            )

        return CausalRelationship(
            cause=cause,
            effect=effect,
            strength=strength,
        )