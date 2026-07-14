from datetime import timedelta

from heos.arbitration import (
    ArbitrationCandidate,
    DecisionArbitrator,
)
from heos.planning import FutureScenario, ScenarioMetrics


def future(
    scenario_id: str,
    score: float,
    confidence: float,
) -> FutureScenario:
    return FutureScenario(
        scenario_id=scenario_id,
        title=scenario_id,
        actions=(),
        metrics=ScenarioMetrics(confidence=confidence),
        score=score,
        reasons=("Example candidate.",),
        horizon=timedelta(minutes=15),
    )


report = DecisionArbitrator().arbitrate(
    (
        ArbitrationCandidate(
            future("charge_ev", 92, 0.96),
            policy_priority=10,
        ),
        ArbitrationCandidate(
            future("charge_battery", 94, 0.91),
            policy_priority=5,
        ),
        ArbitrationCandidate(
            future("export", 70, 0.99),
        ),
    )
)

print("Winner:", report.winner_id)
for item in report.ranking:
    print(item.rank, item.scenario_id, item.reason)

print("Trace:")
for entry in report.trace:
    print(entry.stage, entry.message)
