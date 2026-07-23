from heos.result_verification.adaptive_test import AdaptiveTest


def test_engine_exists():

    engine = AdaptiveTest()

    assert engine is not None
