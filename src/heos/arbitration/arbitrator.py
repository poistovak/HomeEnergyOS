"""Deterministic and explainable scenario arbitration."""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    ArbitrationCandidate,
    ArbitrationReport,
    CandidateRanking,
    DecisionTraceEntry,
)
from .policy import ArbitrationPolicy, DefaultArbitrationPolicy


class DecisionArbitrator:
    """Select one highest-ranked valid future scenario."""

    def __init__(
        self,
        policy: ArbitrationPolicy | None = None,
    ) -> None:
        self._policy = policy or DefaultArbitrationPolicy()

    def arbitrate(
        self,
        candidates: Iterable[ArbitrationCandidate],
    ) -> ArbitrationReport:
        candidate_tuple = tuple(candidates)

        if not candidate_tuple:
            return ArbitrationReport(
                winner=None,
                ranking=(),
                trace=(
                    DecisionTraceEntry(
                        stage="input",
                        message="No candidates were supplied.",
                    ),
                    DecisionTraceEntry(
                        stage="decision",
                        message="No winner selected.",
                    ),
                ),
            )

        ordered = tuple(
            sorted(
                candidate_tuple,
                key=self._policy.sort_key,
                reverse=True,
            )
        )

        valid_candidates = tuple(
            candidate
            for candidate in ordered
            if candidate.valid
        )
        winner = (
            valid_candidates[0].scenario
            if valid_candidates
            else None
        )

        ranking = tuple(
            CandidateRanking(
                scenario_id=candidate.scenario.scenario_id,
                rank=index + 1,
                scenario_score=candidate.scenario.score,
                policy_priority=candidate.policy_priority,
                confidence=candidate.scenario.metrics.confidence,
                valid=candidate.valid,
                reason=self._ranking_reason(candidate),
            )
            for index, candidate in enumerate(ordered)
        )

        trace = self._build_trace(
            ordered=ordered,
            winner_id=winner.scenario_id if winner else None,
        )

        return ArbitrationReport(
            winner=winner,
            ranking=ranking,
            trace=trace,
        )

    @staticmethod
    def _ranking_reason(
        candidate: ArbitrationCandidate,
    ) -> str:
        if not candidate.valid:
            return (
                candidate.rejection_reason
                or "Candidate is invalid."
            )

        return (
            "Valid candidate ranked by policy priority "
            f"{candidate.policy_priority}, score "
            f"{candidate.scenario.score:.3f}, and confidence "
            f"{candidate.scenario.metrics.confidence:.3f}."
        )

    @staticmethod
    def _build_trace(
        *,
        ordered: tuple[ArbitrationCandidate, ...],
        winner_id: str | None,
    ) -> tuple[DecisionTraceEntry, ...]:
        entries: list[DecisionTraceEntry] = [
            DecisionTraceEntry(
                stage="input",
                message=f"Received {len(ordered)} candidates.",
            )
        ]

        for index, candidate in enumerate(ordered, start=1):
            state = "valid" if candidate.valid else "rejected"
            entries.append(
                DecisionTraceEntry(
                    stage="ranking",
                    message=(
                        f"Rank {index}: "
                        f"{candidate.scenario.scenario_id} "
                        f"({state}, priority="
                        f"{candidate.policy_priority}, score="
                        f"{candidate.scenario.score:.3f}, confidence="
                        f"{candidate.scenario.metrics.confidence:.3f})."
                    ),
                )
            )

        entries.append(
            DecisionTraceEntry(
                stage="decision",
                message=(
                    f"Selected winner: {winner_id}."
                    if winner_id is not None
                    else "No valid winner selected."
                ),
            )
        )

        return tuple(entries)
