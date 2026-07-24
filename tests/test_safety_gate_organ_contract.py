from heos.organs.safety_gate.organ import SafetyGateOrgan


def test_organ_exists():

    organ = SafetyGateOrgan()

    assert organ is not None
