from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from heos.release_gate import (
    OperationalReleaseEngine,
    OperationalRequest,
    OperationMode,
    ReadinessEvidence,
    ReleasePolicy,
    standard_manifest,
)


@dataclass(frozen=True, slots=True)
class Control:
    battery_power_kw: float
    ev_charge_kw: float
    hvac_thermal_kw: float


def main() -> None:
    now = datetime.now(UTC)

    candidate = type(
        "Candidate",
        (),
        {
            "candidate_id": "standard:balanced",
            "controls": (Control(1.0, 2.0, 3.0),),
            "objective": "balanced",
        },
    )()
    metrics = type(
        "Metrics",
        (),
        {
            "objective_score": 1.25,
            "violation_count": 0,
            "violation_magnitude": 0.0,
        },
    )()
    selected = type(
        "Evaluation",
        (),
        {"candidate": candidate, "metrics": metrics, "feasible": True},
    )()
    strategy_decision = type(
        "StrategyDecision",
        (),
        {
            "decision_id": "strategy-decision-example",
            "generated_at": now - timedelta(minutes=1),
            "selected": selected,
            "alternatives": (selected,),
            "policy_version": "strategy-policy-1",
            "parameter_version": "twin-parameters-1",
        },
    )()

    manifest = standard_manifest(
        now,
        forecast="forecast-1",
        feedback="feedback-1",
        memory="memory-1",
        digital_twin="digital-twin-1",
        calibration="calibration-1",
        strategy="strategy-1",
        compiler="compiler-1",
        safety="safety-1",
        execution="execution-1",
    )

    engine = OperationalReleaseEngine(
        policy=ReleasePolicy(maximum_mode=OperationMode.ADVISE)
    )
    release = engine.evaluate(
        OperationalRequest(
            strategy_decision=strategy_decision,
            requested_mode=OperationMode.ADVISE,
            evaluated_at=now,
            manifest=manifest,
            readiness=ReadinessEvidence(),
        )
    )

    print(release.status)
    print(release.explanation)
    if release.intent is not None:
        print(release.intent.compiler_target)
        print(release.intent.control_payload)


if __name__ == "__main__":
    main()
