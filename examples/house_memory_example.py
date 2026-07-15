from datetime import UTC, datetime

from heos.feedback.models import ExperienceCandidate, OutcomeClassification, VersionStamp
from heos.memory import HouseMemoryEngine, InMemoryHouseMemoryRepository

now = datetime.now(UTC)
experience = ExperienceCandidate(
    record_id="experience-example",
    decision_record_id="decision-example",
    outcome_record_id="outcome-example",
    comparison_record_id="comparison-example",
    created_at=now,
    features={"pv_kw": 6.2, "load_kw": 2.1},
    targets={"grid_kw": 0.0},
    quality_score=0.94,
    classification=OutcomeClassification.EXCELLENT,
    versions=VersionStamp(
        schema_version="feedback-1",
        forecast_version="forecast-1",
        model_version="model-1",
        policy_version="policy-1",
        compiler_version="compiler-1",
    ),
    explanation="PV surplus covered the household load.",
)

memory = HouseMemoryEngine(InMemoryHouseMemoryRepository())
record = memory.remember(experience, remembered_at=now, tags=("solar", "summer"))
print(record.record_id)
print(memory.recall_similar({"pv_kw": 6.0, "load_kw": 2.0}))
