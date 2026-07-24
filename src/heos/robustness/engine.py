from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from heos.digital_twin import TwinParameters
from heos.strategy import (
    StrategyCandidate,
    StrategyEngine,
    StrategyEvaluation,
    StrategyPolicy,
    StrategyRequest,
)

from .canonical import sha256_digest, stable_id
from .grid import generate_perturbations, perturbation_id
from .models import (
    Perturbation,
    RobustnessCertificate,
    RobustnessPolicy,
    RobustnessRun,
    RobustnessSummary,
    VariantEvaluation,
)
from .scenario import perturb_request


class RobustnessEngine:
    def __init__(
        self,
        parameters: TwinParameters,
        *,
        strategy_policy: StrategyPolicy | None = None,
        robustness_policy: RobustnessPolicy | None = None,
        correction_model: object | None = None,
    ) -> None:
        self._parameters = parameters
        self._strategy_policy = strategy_policy or StrategyPolicy()
        self._robustness_policy = robustness_policy or RobustnessPolicy()
        self._strategy = StrategyEngine(
            parameters,
            policy=self._strategy_policy,
            correction_model=correction_model,
        )

    @property
    def robustness_policy(self) -> RobustnessPolicy:
        return self._robustness_policy

    def evaluate(
        self,
        scenario_id: str,
        candidates: Iterable[StrategyCandidate],
        request: StrategyRequest,
        *,
        generated_at: datetime | None = None,
    ) -> RobustnessRun:
        normalized = tuple(candidates)
        if not normalized:
            raise ValueError("candidates must not be empty")
        baseline_decision = self._strategy.select(normalized, request)
        baseline_candidate = baseline_decision.selected.candidate
        variants = tuple(
            self._evaluate_variant(baseline_candidate, normalized, request, perturbation)
            for perturbation in generate_perturbations(self._robustness_policy)
        )
        summary = self._summarize(variants)
        reasons = self._reasons(summary)
        variants_payload = [item.to_dict() for item in variants]
        variants_digest = sha256_digest(variants_payload)
        timestamp = generated_at or request.generated_at
        certificate_payload = {
            "generated_at": timestamp.isoformat(),
            "scenario_id": scenario_id,
            "baseline_decision_id": baseline_decision.decision_id,
            "baseline_candidate_id": baseline_candidate.candidate_id,
            "strategy_policy_version": baseline_decision.policy_version,
            "parameter_version": baseline_decision.parameter_version,
            "robustness_policy_version": self._robustness_policy.version,
            "robust": not reasons,
            "reasons": list(reasons),
            "summary": summary.to_dict(),
            "variants_digest": variants_digest,
        }
        certificate_digest = sha256_digest(certificate_payload)
        certificate = RobustnessCertificate(
            certificate_id=stable_id("heos-robustness-certificate", certificate_payload),
            generated_at=timestamp,
            scenario_id=scenario_id,
            baseline_decision_id=baseline_decision.decision_id,
            baseline_candidate_id=baseline_candidate.candidate_id,
            strategy_policy_version=baseline_decision.policy_version,
            parameter_version=baseline_decision.parameter_version,
            robustness_policy_version=self._robustness_policy.version,
            robust=not reasons,
            reasons=reasons,
            summary=summary,
            variants_digest=variants_digest,
            certificate_digest=certificate_digest,
            metadata={
                "advisory_only": "true",
                "device_commands_sent": "false",
                "method": "bounded-deterministic-counterfactual-grid",
            },
        )
        return RobustnessRun(certificate=certificate, variants=variants)

    def _evaluate_variant(
        self,
        baseline_candidate: StrategyCandidate,
        candidates: tuple[StrategyCandidate, ...],
        request: StrategyRequest,
        perturbation: Perturbation,
    ) -> VariantEvaluation:
        perturbed = perturb_request(request, perturbation)
        baseline = self._strategy.evaluate(baseline_candidate, perturbed)
        evaluations = tuple(self._strategy.evaluate(item, perturbed) for item in candidates)
        selected = min(evaluations, key=self._ranking_key)
        regret = max(0.0, baseline.metrics.objective_score - selected.metrics.objective_score)
        return VariantEvaluation(
            variant_id=perturbation_id(perturbation),
            perturbation=perturbation,
            baseline_candidate_id=baseline_candidate.candidate_id,
            selected_candidate_id=selected.candidate.candidate_id,
            baseline_feasible=baseline.feasible,
            selected_feasible=selected.feasible,
            selection_stable=selected.candidate.candidate_id == baseline_candidate.candidate_id,
            baseline_score=baseline.metrics.objective_score,
            best_score=selected.metrics.objective_score,
            regret=regret,
            peak_grid_import_kw=baseline.metrics.peak_grid_import_kw,
            final_battery_soc=baseline.trace.final_state.battery_soc,
            final_ev_soc=baseline.trace.final_state.ev_soc,
            trace_id=baseline.trace.trace_id,
        )

    def _ranking_key(self, evaluation: StrategyEvaluation) -> tuple[object, ...]:
        feasibility = 0
        if self._strategy_policy.require_feasible:
            feasibility = 0 if evaluation.feasible else 1
        return (
            feasibility,
            round(evaluation.metrics.objective_score, 12),
            evaluation.candidate.objective.value,
            evaluation.candidate.candidate_id,
        )

    @staticmethod
    def _summarize(variants: tuple[VariantEvaluation, ...]) -> RobustnessSummary:
        count = len(variants)
        return RobustnessSummary(
            variant_count=count,
            feasible_ratio=sum(item.baseline_feasible for item in variants) / count,
            selection_stability=sum(item.selection_stable for item in variants) / count,
            worst_regret=max(item.regret for item in variants),
            worst_objective_score=max(item.baseline_score for item in variants),
            peak_grid_import_kw=max(item.peak_grid_import_kw for item in variants),
            minimum_final_battery_soc=min(item.final_battery_soc for item in variants),
            minimum_final_ev_soc=min(item.final_ev_soc for item in variants),
        )

    def _reasons(self, summary: RobustnessSummary) -> tuple[str, ...]:
        policy = self._robustness_policy
        reasons: list[str] = []
        if summary.feasible_ratio < policy.min_feasible_ratio:
            reasons.append(
                "feasible ratio below policy threshold: "
                f"{summary.feasible_ratio:.6f} < {policy.min_feasible_ratio:.6f}"
            )
        if summary.selection_stability < policy.min_selection_stability:
            reasons.append(
                "selection stability below policy threshold: "
                f"{summary.selection_stability:.6f} < "
                f"{policy.min_selection_stability:.6f}"
            )
        if summary.worst_regret > policy.max_regret:
            reasons.append(
                "worst regret above policy threshold: "
                f"{summary.worst_regret:.6f} > {policy.max_regret:.6f}"
            )
        if summary.minimum_final_ev_soc < policy.min_final_ev_soc:
            reasons.append(
                "minimum final EV SOC below policy threshold: "
                f"{summary.minimum_final_ev_soc:.6f} < {policy.min_final_ev_soc:.6f}"
            )
        if summary.minimum_final_battery_soc < policy.min_final_battery_soc:
            reasons.append(
                "minimum final battery SOC below policy threshold: "
                f"{summary.minimum_final_battery_soc:.6f} < "
                f"{policy.min_final_battery_soc:.6f}"
            )
        return tuple(reasons)
