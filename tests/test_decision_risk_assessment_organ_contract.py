from heos.organs.decision_risk_assessment.organ import DecisionRiskAssessmentOrgan


def test_organ_exists():

    organ = DecisionRiskAssessmentOrgan()

    assert organ is not None
