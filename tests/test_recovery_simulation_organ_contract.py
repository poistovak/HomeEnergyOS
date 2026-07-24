from heos.organs.recovery_simulation.organ import RecoverySimulationOrgan


def test_organ_exists():

    organ = RecoverySimulationOrgan()

    assert organ is not None
