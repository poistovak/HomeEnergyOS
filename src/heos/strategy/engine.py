from __future__ import annotations

import json
from dataclasses import replace
from typing import Iterable, Protocol
from uuid import NAMESPACE_URL, uuid5

from heos.digital_twin import DigitalTwin, TwinParameters

from .models import (
    StrategyCandidate,
    StrategyDecision,
    StrategyEvaluation,
    StrategyPolicy,
    StrategyRequest,
)
from .scoring import score_trace


class NoFeasibleStrategyError(RuntimeError):
    pass


class CalibrationLike(Protocol):
    @property
    def recommended_parameters(self) -> TwinParameters: ...


def parameters_from_calibration(report: CalibrationLike) -> TwinParameters:
    parameters = report.recommended_parameters
    if not isinstance(parameters, TwinParameters):
        raise TypeError("recommended_parameters must be TwinParameters")
    return parameters


class StrategyEngine:
    def __init__(
        self,
        parameters: TwinParameters,
        *,
        policy: StrategyPolicy | None = None,
        correction_model: object | None = None,
    ) -> None:
        self._parameters = parameters
        self._policy = policy or StrategyPolicy()
        self._twin = DigitalTwin(parameters, correction_model=correction_model)

    @property
    def parameters(self) -> TwinParameters:
        return self._parameters

    @property
    def policy(self) -> StrategyPolicy:
        return self._policy

    def evaluate(
        self,
        candidate: StrategyCandidate,
        request: StrategyRequest,
        *,
        rank: int = 1,
    ) -> StrategyEvaluation:
        if len(candidate.controls) != request.horizon:
            raise ValueError("candidate controls must match the request horizon")
        trace = self._twin.simulate(
            request.initial_state,
            candidate.controls,
            request.disturbances,
            step_duration=request.step_duration,
            generated_at=request.generated_at,
            metadata=(
                ("strategy_candidate_id", candidate.candidate_id),
                ("strategy_objective", candidate.objective.value),
                *request.metadata,
            ),
            require_feasible=False,
        )
        metrics = score_trace(
            trace,
            request.expanded_tariffs,
            request.expanded_comfort_bands,
            self._policy,
        )
        feasible = trace.feasible
        verdict = "feasible" if feasible else "infeasible"
        explanation = (
            f"Candidate {candidate.candidate_id} is {verdict}; "
            f"deterministic objective score={metrics.objective_score:.8f}. "
            "This result is advisory and does not command devices."
        )
        return StrategyEvaluation(
            candidate=candidate,
            trace=trace,
            metrics=metrics,
            feasible=feasible,
            rank=rank,
            explanation=explanation,
        )

    def select(
        self,
        candidates: Iterable[StrategyCandidate],
        request: StrategyRequest,
    ) -> StrategyDecision:
        normalized = tuple(candidates)
        if not normalized:
            raise ValueError("candidates must not be empty")
        ids = [item.candidate_id for item in normalized]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate ids must be unique")

        evaluations = tuple(self.evaluate(item, request) for item in normalized)
        if self._policy.require_feasible and not any(item.feasible for item in evaluations):
            raise NoFeasibleStrategyError("no feasible strategy candidate")

        ranked = sorted(evaluations, key=self._ranking_key)
        alternatives = tuple(replace(item, rank=index) for index, item in enumerate(ranked, 1))
        selected = alternatives[0]
        decision_id = self._decision_id(alternatives, request)
        explanation = (
            f"Selected {selected.candidate.candidate_id} from {len(alternatives)} candidates "
            f"using policy {self._policy.version}. Feasibility is ranked before score when "
            "required; ties are resolved deterministically. The decision is advisory."
        )
        return StrategyDecision(
            decision_id=decision_id,
            generated_at=request.generated_at,
            selected=selected,
            alternatives=alternatives,
            policy_version=self._policy.version,
            parameter_version=self._parameters.version,
            explanation=explanation,
        )

    def _ranking_key(self, evaluation: StrategyEvaluation) -> tuple[object, ...]:
        feasibility_rank = 0
        if self._policy.require_feasible:
            feasibility_rank = 0 if evaluation.feasible else 1
        return (
            feasibility_rank,
            round(evaluation.metrics.objective_score, 12),
            evaluation.candidate.objective.value,
            evaluation.candidate.candidate_id,
        )

    def _decision_id(
        self,
        evaluations: tuple[StrategyEvaluation, ...],
        request: StrategyRequest,
    ) -> str:
        payload = {
            "generated_at": request.generated_at.isoformat(),
            "policy": self._policy.version,
            "parameters": self._parameters.version,
            "initial_state_at": request.initial_state.observed_at.isoformat(),
            "candidates": [
                {
                    "candidate_id": item.candidate.candidate_id,
                    "trace_id": item.trace.trace_id,
                    "rank": item.rank,
                    "score": round(item.metrics.objective_score, 12),
                    "feasible": item.feasible,
                }
                for item in evaluations
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return str(uuid5(NAMESPACE_URL, f"heos-strategy:{canonical}"))
