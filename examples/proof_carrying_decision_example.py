from datetime import UTC, datetime

from heos.proof_carrying import ProofCarryingDecisionEngine, replay_envelope

# `release_decision` is the released M20 object produced by OperationalReleaseGate.
# It is intentionally not constructed here because production code should pass the real object.
release_decision = ...

engine = ProofCarryingDecisionEngine()
certified = engine.certify(
    release_decision,
    issued_at=datetime.now(UTC),
    state_snapshot={
        "pv_kw": 6.2,
        "grid_kw": 0.4,
        "battery_soc": 0.64,
        "ev_soc": 0.42,
    },
    manifest_versions={
        "forecast": "forecast-1",
        "feedback": "feedback-1",
        "memory": "memory-1",
        "digital_twin": "digital-twin-1",
        "calibration": "calibration-1",
        "strategy": "strategy-1",
        "compiler": "compiler-1",
        "safety": "safety-1",
        "execution": "execution-1",
        "release_gate": "release-gate-1",
    },
    rejected_alternatives=(
        {"candidate_id": "cost-first", "objective_score": 1.31},
        {"candidate_id": "comfort-first", "objective_score": 1.55},
    ),
)

report = engine.verify(certified, verified_at=certified.certificate.issued_at)
assert report.valid

replay = replay_envelope(certified)
print(certified.certificate.certificate_id)
print(replay.replay_token)
