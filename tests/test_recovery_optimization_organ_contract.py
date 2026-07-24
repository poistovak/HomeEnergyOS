from heos.organs.recovery_optimization.organ import RecoveryOptimizationOrgan


def test_organ_exists():

    organ = RecoveryOptimizationOrgan()

    assert organ is not None
