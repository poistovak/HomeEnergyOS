from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    similarity: float
    success: bool

    def __post_init__(self) -> None:
        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError(
                "similarity must be between 0 and 1"
            )


@dataclass(frozen=True, slots=True)
class WeightedEvidence:
    confidence: float
    samples: int
    total_weight: float


class WeightedEvidenceEngine:

    def evaluate(
        self,
        evidence: list[Evidence],
    ) -> WeightedEvidence:
        if not evidence:
            raise ValueError(
                "evidence must not be empty"
            )

        total_weight = sum(
            item.similarity
            for item in evidence
        )

        if total_weight == 0.0:
            return WeightedEvidence(
                confidence=0.0,
                samples=len(evidence),
                total_weight=0.0,
            )

        successful_weight = sum(
            item.similarity
            for item in evidence
            if item.success
        )

        confidence = successful_weight / total_weight

        return WeightedEvidence(
            confidence=confidence,
            samples=len(evidence),
            total_weight=total_weight,
        )