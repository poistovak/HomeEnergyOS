from heos.organs.decision_confidence.organ import DecisionConfidenceOrgan


def test_organ_exists():

    organ = DecisionConfidenceOrgan()

    assert organ is not None
