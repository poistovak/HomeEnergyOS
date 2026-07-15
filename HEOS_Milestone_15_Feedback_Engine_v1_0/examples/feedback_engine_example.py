from datetime import UTC, datetime, timedelta

from heos.feedback import (
    ActionRecord,
    DecisionRecord,
    ExecutionStatus,
    FeedbackEngine,
    InMemoryFeedbackRepository,
    OutcomeRecord,
    VersionStamp,
)

start = datetime.now(UTC).replace(microsecond=0)
end = start + timedelta(hours=1)
versions = VersionStamp("1.0", "m14-1.0", "physics-0.1", "policy-1", "m10-1.0")
decision = DecisionRecord(
    record_id="decision-record-1",
    decision_id="decision-1",
    scenario_id="charge_ev_now",
    committed_at=start,
    effective_from=start,
    effective_until=end,
    predicted_state={"battery_soc": 60.0, "grid_energy_kwh": 1.0},
    planned_actions=(ActionRecord("ev.charger", "set_power", 3000, "W"),),
    versions=versions,
)
outcome = OutcomeRecord(
    record_id="outcome-record-1",
    decision_record_id=decision.record_id,
    observed_at=end,
    window_start=start,
    window_end=end,
    actual_state={"battery_soc": 59.0, "grid_energy_kwh": 1.1},
    executed_actions=(ActionRecord("ev.charger", "set_power", 3000, "W"),),
    status=ExecutionStatus.COMPLETED,
)
repository = InMemoryFeedbackRepository()
engine = FeedbackEngine(repository)
engine.capture_decision(decision)
engine.capture_outcome(outcome)
comparison = engine.compare(decision.record_id, outcome.record_id, compared_at=end)
experience = engine.materialize_experience(comparison.record_id, created_at=end)
print(comparison.explanation)
print(f"M16 candidate quality: {experience.quality_score:.3f}")
