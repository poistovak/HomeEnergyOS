from heos.organs.recovery_strategy.organ import RecoveryStrategyOrgan


def test_organ_exists():

    organ = RecoveryStrategyOrgan()

    assert organ is not None
