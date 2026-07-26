from __future__ import annotations

from dataclasses import dataclass

from .context_similarity import ContextSimilarityEngine
from .decision_experience import DecisionExperienceMemory
from .reasoning_confidence import ReasoningConfidenceEngine
from .reasoning_orchestrator import (
    ReasoningOrchestrator,
    ReasoningResult,
)
from .weighted_evidence import (
    Evidence,
    WeightedEvidenceEngine,
)


@dataclass(frozen=True, slots=True)
class ExperienceReasoner:
    memory: DecisionExperienceMemory
    similarity_engine: ContextSimilarityEngine
    evidence_engine: WeightedEvidenceEngine
    confidence_engine: ReasoningConfidenceEngine
    orchestrator: ReasoningOrchestrator
    minimum_similarity: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_similarity <= 1.0:
            raise ValueError(
                "minimum_similarity must be between 0 and 1"
            )

    def reason(
        self,
        context: dict[str, object],
    ) -> ReasoningResult | None:
        if not context:
            raise ValueError(
                "context must not be empty"
            )

        decisions: dict[str, list[Evidence]] = {}

        for experience in self.memory.all():
            similarity = self.similarity_engine.compare(
                experience.context,
                context,
            ).score

            if similarity < self.minimum_similarity:
                continue

            decisions.setdefault(
                experience.decision,
                [],
            ).append(
                Evidence(
                    similarity=similarity,
                    success=experience.success,
                )
            )

        if not decisions:
            return None

        best_decision: str | None = None
        best_confidence = -1.0

        for decision, evidence in decisions.items():
            weighted = self.evidence_engine.evaluate(
                evidence
            )

            confidence = self.confidence_engine.evaluate(
                weighted.confidence
            ).confidence

            if confidence > best_confidence:
                best_decision = decision
                best_confidence = confidence

        if best_decision is None:
            return None

        return self.orchestrator.create_result(
            decision=best_decision,
            confidence=best_confidence,
        )