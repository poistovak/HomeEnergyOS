from __future__ import annotations

import json
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .inspection import (
    control_payload,
    decision_shape_errors,
    objective_value,
    selected_candidate,
    selected_evaluation,
    selected_metrics,
)
from .models import (
    ExecutionIntent,
    GateCode,
    GateResult,
    OperationalRequest,
    OperationMode,
    ReadinessEvidence,
    ReleaseDecision,
    ReleasePolicy,
    ReleaseStatus,
    mode_rank,
)

_READINESS_GATES = (
    ("forecast_ready", GateCode.FORECAST_READY),
    ("feedback_ready", GateCode.FEEDBACK_READY),
    ("memory_ready", GateCode.MEMORY_READY),
    ("digital_twin_ready", GateCode.DIGITAL_TWIN_READY),
    ("calibration_ready", GateCode.CALIBRATION_READY),
    ("strategy_ready", GateCode.STRATEGY_READY),
    ("compiler_ready", GateCode.COMPILER_READY),
    ("safety_ready", GateCode.SAFETY_READY),
    ("executor_ready", GateCode.EXECUTOR_READY),
)


class OperationalReleaseGate:
    def __init__(self, policy: ReleasePolicy | None = None) -> None:
        self._policy = policy or ReleasePolicy()

    @property
    def policy(self) -> ReleasePolicy:
        return self._policy

    def review(self, request: OperationalRequest) -> ReleaseDecision:
        gates: list[GateResult] = []
        hard_rejection = False

        manifest_passed = request.manifest.complete
        gates.append(
            GateResult(
                GateCode.MANIFEST_COMPLETE,
                manifest_passed,
                True,
                (
                    "required component versions are present"
                    if manifest_passed
                    else "missing components: "
                    + ", ".join(request.manifest.missing_required_components)
                ),
            )
        )

        mode_passed = mode_rank(request.requested_mode) <= mode_rank(self._policy.maximum_mode)
        hard_rejection = hard_rejection or not mode_passed
        gates.append(
            GateResult(
                GateCode.MODE_ALLOWED,
                mode_passed,
                True,
                (
                    f"{request.requested_mode.value} is allowed"
                    if mode_passed
                    else (
                        f"{request.requested_mode.value} exceeds "
                        f"{self._policy.maximum_mode.value}"
                    )
                ),
            )
        )

        shape_errors = decision_shape_errors(
            request.strategy_decision,
            self._policy.minimum_alternatives,
        )
        shape_passed = not shape_errors
        hard_rejection = hard_rejection or not shape_passed
        gates.append(
            GateResult(
                GateCode.DECISION_SHAPE,
                shape_passed,
                True,
                "strategy decision shape is valid"
                if shape_passed
                else "; ".join(shape_errors),
            )
        )

        source_decision_id = str(
            getattr(request.strategy_decision, "decision_id", "invalid-strategy-decision")
        )

        if shape_passed:
            self._append_strategy_gates(gates, request)
        else:
            self._append_unavailable_strategy_gates(gates)

        self._append_readiness_gates(gates, request.readiness)
        self._append_approval_gates(gates, request)

        failed = tuple(item for item in gates if not item.passed)
        if hard_rejection:
            status = ReleaseStatus.REJECTED
        elif failed:
            status = ReleaseStatus.HELD
        else:
            status = ReleaseStatus.RELEASED

        release_id = self._release_id(request, gates, source_decision_id)
        intent = (
            self._build_intent(request, release_id, source_decision_id)
            if status is ReleaseStatus.RELEASED
            else None
        )
        explanation = self._explanation(status, failed)

        return ReleaseDecision(
            release_id=release_id,
            source_decision_id=source_decision_id,
            evaluated_at=request.evaluated_at,
            requested_mode=request.requested_mode,
            status=status,
            gates=tuple(gates),
            policy_version=self._policy.version,
            manifest_schema_version=request.manifest.schema_version,
            intent=intent,
            explanation=explanation,
            metadata=request.metadata,
        )

    def _append_strategy_gates(
        self,
        gates: list[GateResult],
        request: OperationalRequest,
    ) -> None:
        decision = request.strategy_decision
        generated_at = decision.generated_at
        age = request.evaluated_at - generated_at
        freshness_passed = (
            age <= self._policy.maximum_decision_age
            and age >= -self._policy.maximum_future_skew
        )
        gates.append(
            GateResult(
                GateCode.DECISION_FRESH,
                freshness_passed,
                True,
                (
                    f"decision age {age.total_seconds():.3f}s is within policy"
                    if freshness_passed
                    else f"decision age {age.total_seconds():.3f}s is outside policy"
                ),
            )
        )

        selected = selected_evaluation(decision)
        feasible = bool(selected.feasible)
        feasibility_passed = feasible or not self._policy.require_feasible
        gates.append(
            GateResult(
                GateCode.STRATEGY_FEASIBLE,
                feasibility_passed,
                True,
                "selected strategy is feasible"
                if feasible
                else "selected strategy is infeasible",
            )
        )

        metrics = selected_metrics(decision)
        score = float(metrics.objective_score)
        maximum_score = self._policy.maximum_objective_score
        score_passed = maximum_score is None or score <= maximum_score
        gates.append(
            GateResult(
                GateCode.STRATEGY_SCORE,
                score_passed,
                False,
                (
                    f"objective score {score:.8f} is accepted"
                    if score_passed
                    else f"objective score {score:.8f} exceeds {maximum_score:.8f}"
                ),
            )
        )

        violation_count = int(metrics.violation_count)
        violation_magnitude = float(metrics.violation_magnitude)
        zero_violations = violation_count == 0 and violation_magnitude == 0.0
        violation_passed = zero_violations or not self._policy.require_zero_violations
        gates.append(
            GateResult(
                GateCode.ZERO_VIOLATIONS,
                violation_passed,
                True,
                (
                    "selected strategy has no simulated violations"
                    if zero_violations
                    else (
                        f"selected strategy has {violation_count} violations "
                        f"with magnitude {violation_magnitude:.8f}"
                    )
                ),
            )
        )

        objective = objective_value(decision)
        objective_passed = (
            not self._policy.allowed_objectives
            or objective in self._policy.allowed_objectives
        )
        gates.append(
            GateResult(
                GateCode.OBJECTIVE_ALLOWED,
                objective_passed,
                False,
                (
                    f"objective {objective} is allowed"
                    if objective_passed
                    else f"objective {objective} is not allowed"
                ),
            )
        )

        policy_version = str(decision.policy_version)
        policy_version_passed = (
            not self._policy.allowed_policy_versions
            or policy_version in self._policy.allowed_policy_versions
        )
        gates.append(
            GateResult(
                GateCode.POLICY_VERSION_ALLOWED,
                policy_version_passed,
                True,
                (
                    f"policy version {policy_version} is allowed"
                    if policy_version_passed
                    else f"policy version {policy_version} is not allowed"
                ),
            )
        )

        parameter_version = str(decision.parameter_version)
        parameter_version_passed = (
            not self._policy.allowed_parameter_versions
            or parameter_version in self._policy.allowed_parameter_versions
        )
        gates.append(
            GateResult(
                GateCode.PARAMETER_VERSION_ALLOWED,
                parameter_version_passed,
                True,
                (
                    f"parameter version {parameter_version} is allowed"
                    if parameter_version_passed
                    else f"parameter version {parameter_version} is not allowed"
                ),
            )
        )

    @staticmethod
    def _append_unavailable_strategy_gates(gates: list[GateResult]) -> None:
        for code in (
            GateCode.DECISION_FRESH,
            GateCode.STRATEGY_FEASIBLE,
            GateCode.STRATEGY_SCORE,
            GateCode.ZERO_VIOLATIONS,
            GateCode.OBJECTIVE_ALLOWED,
            GateCode.POLICY_VERSION_ALLOWED,
            GateCode.PARAMETER_VERSION_ALLOWED,
        ):
            gates.append(
                GateResult(
                    code,
                    False,
                    True,
                    "not evaluated because strategy decision shape is invalid",
                )
            )

    @staticmethod
    def _append_readiness_gates(
        gates: list[GateResult],
        readiness: ReadinessEvidence,
    ) -> None:
        for attribute, code in _READINESS_GATES:
            ready = bool(getattr(readiness, attribute))
            component = code.value.removesuffix("_ready")
            gates.append(
                GateResult(
                    code,
                    ready,
                    True,
                    f"{component} is ready" if ready else f"{component} is not ready",
                )
            )

    def _append_approval_gates(
        self,
        gates: list[GateResult],
        request: OperationalRequest,
    ) -> None:
        operator_required = (
            request.requested_mode is OperationMode.SUPERVISED
            and self._policy.require_operator_approval_for_supervised
        ) or (
            request.requested_mode is OperationMode.AUTONOMOUS
            and self._policy.require_operator_approval_for_autonomous
        )
        operator_passed = not operator_required or request.operator_approved
        gates.append(
            GateResult(
                GateCode.OPERATOR_APPROVAL,
                operator_passed,
                True,
                (
                    "operator approval is present or not required"
                    if operator_passed
                    else "operator approval is required"
                ),
            )
        )

        autonomy_required = request.requested_mode is OperationMode.AUTONOMOUS
        autonomy_passed = not autonomy_required or request.autonomy_authorized
        gates.append(
            GateResult(
                GateCode.AUTONOMY_AUTHORIZATION,
                autonomy_passed,
                True,
                (
                    "autonomy authorization is present or not required"
                    if autonomy_passed
                    else "autonomy authorization is required"
                ),
            )
        )

    def _build_intent(
        self,
        request: OperationalRequest,
        release_id: str,
        source_decision_id: str,
    ) -> ExecutionIntent:
        candidate = selected_candidate(request.strategy_decision)
        controls = tuple(candidate.controls)
        first_control = controls[0]
        payload = control_payload(first_control)
        intent_id = str(uuid5(NAMESPACE_URL, f"heos-intent:{release_id}"))

        return ExecutionIntent(
            intent_id=intent_id,
            source_decision_id=source_decision_id,
            candidate_id=str(candidate.candidate_id),
            requested_mode=request.requested_mode,
            created_at=request.evaluated_at,
            not_after=request.evaluated_at + self._policy.maximum_decision_age,
            compiler_target="heos.decision_compiler",
            control_payload=payload,
            metadata=(
                ("release_id", release_id),
                ("release_policy_version", self._policy.version),
                *request.metadata,
            ),
        )

    def _release_id(
        self,
        request: OperationalRequest,
        gates: list[GateResult],
        source_decision_id: str,
    ) -> str:
        payload: dict[str, Any] = {
            "source_decision_id": source_decision_id,
            "evaluated_at": request.evaluated_at.isoformat(),
            "requested_mode": request.requested_mode.value,
            "manifest": request.manifest.versions,
            "manifest_schema": request.manifest.schema_version,
            "policy": self._policy.version,
            "operator_approved": request.operator_approved,
            "autonomy_authorized": request.autonomy_authorized,
            "metadata": request.metadata,
            "gates": [
                {
                    "code": item.code.value,
                    "passed": item.passed,
                    "critical": item.critical,
                    "detail": item.detail,
                }
                for item in gates
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return str(uuid5(NAMESPACE_URL, f"heos-release:{canonical}"))

    @staticmethod
    def _explanation(
        status: ReleaseStatus,
        failed: tuple[GateResult, ...],
    ) -> str:
        if status is ReleaseStatus.RELEASED:
            return (
                "Operational release gate passed. The emitted intent targets the "
                "deterministic Decision Compiler and does not command devices directly."
            )
        failed_codes = ", ".join(item.code.value for item in failed)
        if status is ReleaseStatus.REJECTED:
            return f"Operational request rejected by hard gates: {failed_codes}."
        return f"Operational request held until gates pass: {failed_codes}."
