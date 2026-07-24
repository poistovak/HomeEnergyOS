from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from heos.compiler import DecisionCompiler
from heos.execution import ExecutionRuntime
from heos.execution.drivers import DryRunExecutionDriver
from heos.feedback import (
    ActionRecord,
    DecisionRecord,
    FeedbackEngine,
    InMemoryFeedbackRepository,
    OutcomeRecord,
    VersionStamp,
)
from heos.feedback import (
    ExecutionStatus as FeedbackExecutionStatus,
)
from heos.kernel import EnergyBalance, KernelHealth, KernelSnapshot
from heos.memory import HouseMemoryEngine, InMemoryHouseMemoryRepository
from heos.proof_carrying import (
    CertifiedDecision,
    ProofCarryingDecisionEngine,
    replay_envelope,
)
from heos.release_gate import (
    OperationalReleaseGate,
    OperationalRequest,
    OperationMode,
    standard_manifest,
)
from heos.safety import SafetyContext, SafetyEngine
from heos.strategy import StrategyDecision, StrategyEngine

from .canonical import sha256_digest
from .models import DemoResult, DemoStage
from .scenarios import DemoScenario, sunny_surplus_scenario

DEMO_VERSION = "glass-box-demo-1"


@dataclass(frozen=True, slots=True)
class DemoRun:
    result: DemoResult
    certified_decision: CertifiedDecision
    audit_payload: dict[str, Any]


def _stage(name: str, passed: bool, detail: str) -> DemoStage:
    return DemoStage(name=name, status="pass" if passed else "fail", detail=detail)


def _strategy(scenario: DemoScenario) -> StrategyDecision:
    return StrategyEngine(scenario.parameters, policy=scenario.policy).select(
        scenario.candidates,
        scenario.request,
    )


def _manifest(scenario: DemoScenario):
    return standard_manifest(
        scenario.request.generated_at,
        forecast="forecast-core-1",
        feedback="feedback-engine-1",
        memory="house-memory-1",
        digital_twin="digital-twin-1",
        calibration="calibration-engine-1",
        strategy="strategy-engine-1",
        compiler="decision-compiler-1",
        safety="safety-engine-1",
        execution="execution-runtime-1",
    )


def _proof(
    scenario: DemoScenario,
    decision: StrategyDecision,
    release_decision: Any,
) -> tuple[CertifiedDecision, bool, str]:
    manifest = _manifest(scenario)
    versions = dict(manifest.versions)
    versions["release_gate"] = "operational-release-gate-1"
    state = {
        "timestamp": scenario.request.generated_at,
        "grid_kw": decision.selected.trace.steps[0].grid_import_kw,
        "pv_kw": scenario.request.disturbances[0].pv_kw,
        "battery_soc": scenario.request.initial_state.battery_soc,
        "ev_soc": scenario.request.initial_state.ev_soc,
        "indoor_c": scenario.request.initial_state.indoor_temp_c,
    }
    rejected = tuple(
        {
            "candidate_id": item.candidate.candidate_id,
            "objective_score": item.metrics.objective_score,
        }
        for item in decision.alternatives
        if item.candidate.candidate_id != decision.selected.candidate.candidate_id
    )
    engine = ProofCarryingDecisionEngine()
    certified = engine.certify(
        release_decision,
        state_snapshot=state,
        manifest_versions=versions,
        rejected_alternatives=rejected,
        issued_at=scenario.request.generated_at,
        metadata=(("demo", DEMO_VERSION), ("scenario", scenario.scenario_id)),
    )
    verification = engine.verify(certified, verified_at=scenario.request.generated_at)
    envelope = replay_envelope(certified)
    return certified, verification.valid, envelope.replay_token


def _feedback_and_memory(
    scenario: DemoScenario,
    decision: StrategyDecision,
    actions: tuple[ActionRecord, ...],
) -> tuple[str, float, str, str, float]:
    feedback_repository = InMemoryFeedbackRepository()
    feedback = FeedbackEngine(feedback_repository)
    generated = scenario.request.generated_at
    final = decision.selected.trace.final_state
    decision_record = DecisionRecord(
        record_id="m22-decision-record",
        decision_id=decision.decision_id,
        scenario_id=scenario.scenario_id,
        committed_at=generated,
        effective_from=generated,
        effective_until=generated + timedelta(hours=4),
        predicted_state={
            "battery_soc": final.battery_soc,
            "ev_soc": final.ev_soc,
            "grid_import_kwh": final.grid_import_kwh,
            "indoor_temp_c": final.indoor_temp_c,
        },
        planned_actions=actions,
        versions=VersionStamp(
            schema_version="feedback-1",
            forecast_version="forecast-core-1",
            model_version=scenario.parameters.version,
            policy_version=scenario.policy.version,
            compiler_version="decision-compiler-1",
        ),
        context={"demo": DEMO_VERSION, "weather": "sunny-surplus"},
        correlation_id=decision.decision_id,
    )
    outcome_record = OutcomeRecord(
        record_id="m22-outcome-record",
        decision_record_id=decision_record.record_id,
        observed_at=generated + timedelta(hours=4),
        window_start=generated,
        window_end=generated + timedelta(hours=4),
        actual_state={
            "battery_soc": final.battery_soc,
            "ev_soc": max(0.0, final.ev_soc - 0.004),
            "grid_import_kwh": final.grid_import_kwh + 0.01,
            "indoor_temp_c": final.indoor_temp_c - 0.02,
        },
        executed_actions=actions,
        status=FeedbackExecutionStatus.COMPLETED,
        constraints_satisfied=True,
        notes=("Deterministic dry-run outcome for M22.",),
    )
    feedback.capture_decision(decision_record)
    feedback.capture_outcome(outcome_record)
    comparison = feedback.compare(
        decision_record.record_id,
        outcome_record.record_id,
        compared_at=generated + timedelta(hours=4),
    )
    experience = feedback.materialize_experience(
        comparison.record_id,
        created_at=generated + timedelta(hours=4),
    )
    memory = HouseMemoryEngine(InMemoryHouseMemoryRepository())
    record = memory.remember(
        experience,
        remembered_at=generated + timedelta(hours=4),
        tags=("demo", "ev", "solar"),
    )
    matches = memory.recall_similar(experience.features, limit=1, min_similarity=0.99)
    if len(matches) != 1:
        raise RuntimeError("house memory failed to recall the stored experience")
    return (
        comparison.classification.value,
        comparison.metrics.overall_score,
        record.record_id,
        record.fingerprint.digest,
        record.quality_score,
    )


def _audit_payload(
    *,
    scenario: DemoScenario,
    decision: StrategyDecision,
    release_decision: Any,
    certified: CertifiedDecision,
    proof_valid: bool,
    replay_token: str,
    plan: Any,
    safety_report: Any,
    runtime_report: Any,
    feedback_classification: str,
    feedback_score: float,
    memory_record_id: str,
    memory_fingerprint: str,
    memory_quality: float,
    stages: tuple[DemoStage, ...],
) -> dict[str, Any]:
    return {
        "demo_version": DEMO_VERSION,
        "scenario_id": scenario.scenario_id,
        "generated_at": scenario.request.generated_at.isoformat(),
        "strategy": {
            "decision_id": decision.decision_id,
            "selected": decision.selected.candidate.candidate_id,
            "alternatives": [
                {
                    "candidate_id": item.candidate.candidate_id,
                    "objective_score": item.metrics.objective_score,
                    "feasible": item.feasible,
                }
                for item in decision.alternatives
            ],
            "explanation": decision.explanation,
        },
        "release_gate": {
            "release_id": release_decision.release_id,
            "status": release_decision.status.value,
            "failed_gates": [item.code.value for item in release_decision.failed_gates],
            "control_payload": dict(release_decision.intent.control_payload),
        },
        "proof": {
            "certificate_id": certified.certificate.certificate_id,
            "valid": proof_valid,
            "replay_token": replay_token,
            "claims": [
                {"code": claim.code.value, "passed": claim.passed, "detail": claim.detail}
                for claim in certified.certificate.claims
            ],
        },
        "compiler": {
            "scenario_id": plan.scenario_id,
            "steps": [
                {"type": step.step_type.value, "description": step.description}
                for step in plan.steps
            ],
        },
        "safety": {
            "verdict": safety_report.verdict.value,
            "findings": [
                {
                    "rule_id": finding.rule_id,
                    "verdict": finding.verdict.value,
                    "reason": finding.reason,
                }
                for finding in safety_report.findings
            ],
        },
        "execution": {
            "status": runtime_report.status.value,
            "completed_steps": runtime_report.completed_steps,
            "total_steps": runtime_report.total_steps,
            "messages": [entry.message for entry in runtime_report.journal],
        },
        "feedback": {
            "classification": feedback_classification,
            "score": feedback_score,
        },
        "memory": {
            "record_id": memory_record_id,
            "fingerprint": memory_fingerprint,
            "quality": memory_quality,
        },
        "stages": [stage.to_dict() for stage in stages],
    }


def run_demo(scenario: DemoScenario | None = None) -> DemoRun:
    active = scenario or sunny_surplus_scenario()
    stages: list[DemoStage] = []

    decision = _strategy(active)
    stages.append(
        _stage(
            "strategy",
            decision.selected.feasible,
            f"Selected {decision.selected.candidate.candidate_id} from {len(active.candidates)} candidates.",
        )
    )

    manifest = _manifest(active)
    release_decision = OperationalReleaseGate().review(
        OperationalRequest(
            strategy_decision=decision,
            requested_mode=OperationMode.ADVISE,
            evaluated_at=active.request.generated_at,
            manifest=manifest,
            metadata=(("demo", DEMO_VERSION),),
        )
    )
    stages.append(
        _stage(
            "release_gate",
            release_decision.released,
            release_decision.explanation,
        )
    )
    if not release_decision.released or release_decision.intent is None:
        raise RuntimeError("operational release gate did not release the demo decision")

    certified, proof_valid, replay_token = _proof(active, decision, release_decision)
    stages.append(
        _stage(
            "proof",
            proof_valid,
            f"Certificate {certified.certificate.certificate_id} verified.",
        )
    )

    payload = dict(release_decision.intent.control_payload)
    compiler_scenario = "charge_ev_now" if payload.get("ev_charge_kw", 0.0) > 0.0 else "observe_only"
    plan = DecisionCompiler().compile(compiler_scenario)
    stages.append(
        _stage("compiler", bool(plan.steps), f"Compiled {len(plan.steps)} deterministic steps.")
    )

    first_step = decision.selected.trace.steps[0]
    projected_import_w = first_step.grid_import_kw * 1000.0
    kernel = KernelSnapshot(
        health=KernelHealth.READY,
        balance=EnergyBalance(
            production_w=active.request.disturbances[0].pv_kw * 1000.0,
            consumption_w=(
                active.request.disturbances[0].base_load_kw
                + payload.get("ev_charge_kw", 0.0)
            )
            * 1000.0,
            storage_charge_w=max(0.0, payload.get("battery_power_kw", 0.0)) * 1000.0,
            storage_discharge_w=max(0.0, -payload.get("battery_power_kw", 0.0)) * 1000.0,
            grid_import_w=projected_import_w,
            grid_export_w=max(0.0, -first_step.grid_power_kw) * 1000.0,
        ),
        resource_count=4,
        flow_count=3,
        created_at=active.request.generated_at,
    )
    safety_report = SafetyEngine().evaluate(
        SafetyContext(
            plan=plan,
            kernel=kernel,
            projected_grid_import_w=projected_import_w,
            maximum_grid_import_w=active.parameters.grid_max_import_kw * 1000.0,
        )
    )
    stages.append(
        _stage("safety", safety_report.allowed, f"Safety verdict: {safety_report.verdict.value}.")
    )
    if not safety_report.allowed:
        raise RuntimeError("safety engine denied the demo execution plan")

    runtime_report = ExecutionRuntime(DryRunExecutionDriver()).run(plan)
    stages.append(
        _stage(
            "execution",
            runtime_report.successful,
            f"Dry-run completed {runtime_report.completed_steps}/{runtime_report.total_steps} steps.",
        )
    )

    actions = tuple(
        ActionRecord(
            resource_id="home-control",
            action=key,
            target=value,
            unit="kW",
            metadata={"source": "m22-demo"},
        )
        for key, value in release_decision.intent.control_payload
    )
    (
        feedback_classification,
        feedback_score,
        memory_record_id,
        memory_fingerprint,
        memory_quality,
    ) = _feedback_and_memory(active, decision, actions)
    stages.append(
        _stage(
            "feedback",
            feedback_score >= 0.90,
            f"Outcome classified as {feedback_classification}; score {feedback_score:.3f}.",
        )
    )
    stages.append(
        _stage(
            "memory",
            bool(memory_record_id),
            f"Experience stored as {memory_record_id}.",
        )
    )

    frozen_stages = tuple(stages)
    audit = _audit_payload(
        scenario=active,
        decision=decision,
        release_decision=release_decision,
        certified=certified,
        proof_valid=proof_valid,
        replay_token=replay_token,
        plan=plan,
        safety_report=safety_report,
        runtime_report=runtime_report,
        feedback_classification=feedback_classification,
        feedback_score=feedback_score,
        memory_record_id=memory_record_id,
        memory_fingerprint=memory_fingerprint,
        memory_quality=memory_quality,
        stages=frozen_stages,
    )
    digest = sha256_digest(audit)
    success = all(stage.passed for stage in frozen_stages)
    result = DemoResult(
        demo_version=DEMO_VERSION,
        scenario_id=active.scenario_id,
        generated_at=active.request.generated_at,
        success=success,
        selected_strategy=decision.selected.candidate.candidate_id,
        strategy_decision_id=decision.decision_id,
        alternative_scores=tuple(
            (item.candidate.candidate_id, item.metrics.objective_score)
            for item in decision.alternatives
        ),
        release_id=release_decision.release_id,
        release_status=release_decision.status.value,
        certificate_id=certified.certificate.certificate_id,
        proof_valid=proof_valid,
        replay_token=replay_token,
        compiler_scenario=plan.scenario_id,
        execution_steps=tuple(step.description for step in plan.steps),
        safety_verdict=safety_report.verdict.value,
        execution_status=runtime_report.status.value,
        execution_messages=tuple(entry.message for entry in runtime_report.journal),
        feedback_classification=feedback_classification,
        feedback_score=feedback_score,
        memory_record_id=memory_record_id,
        memory_fingerprint=memory_fingerprint,
        memory_quality=memory_quality,
        stages=frozen_stages,
        audit_digest=digest,
        metadata={
            "mode": release_decision.requested_mode.value,
            "output": "deterministic",
            "safety": "never bypassed",
        },
    )
    return DemoRun(result=result, certified_decision=certified, audit_payload=audit)
