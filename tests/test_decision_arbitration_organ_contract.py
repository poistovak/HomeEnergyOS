from heos.organs.decision_arbitration.organ import DecisionArbitrationOrgan


def test_organ_exists():

    organ = DecisionArbitrationOrgan()

    assert organ is not None
