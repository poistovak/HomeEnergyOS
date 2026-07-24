from heos.organs.predictive_recovery.organ import PredictiveRecoveryOrgan


def test_organ_exists():

    organ = PredictiveRecoveryOrgan()

    assert organ is not None
