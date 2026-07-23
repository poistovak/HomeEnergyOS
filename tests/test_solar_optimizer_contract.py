from heos.result_verification.solar_optimizer import SolarOptimizer


def test_engine_exists():

    engine = SolarOptimizer()

    assert engine is not None
