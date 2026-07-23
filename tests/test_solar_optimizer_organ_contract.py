from heos.organs.solar_optimizer.organ import SolarOptimizerOrgan


def test_organ_exists():

    organ = SolarOptimizerOrgan()

    assert organ is not None
