from heos.result_verification import (
    ContextAwareDecisionRecommender,
    DecisionExperience,
    DecisionExperienceMemory,
    DecisionMemoryBridge,
    Evidence,
    ExperienceReasoner,
    LearningBridge,
    LearningRecorder,
    WeightedEvidence,
    WeightedEvidenceEngine,
)


def test_new_reasoning_components_are_public():
    assert ContextAwareDecisionRecommender is not None
    assert DecisionExperience is not None
    assert DecisionExperienceMemory is not None
    assert DecisionMemoryBridge is not None
    assert Evidence is not None
    assert ExperienceReasoner is not None
    assert LearningBridge is not None
    assert LearningRecorder is not None
    assert WeightedEvidence is not None
    assert WeightedEvidenceEngine is not None