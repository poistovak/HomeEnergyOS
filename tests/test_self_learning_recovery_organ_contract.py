from heos.organs.self_learning_recovery.organ import SelfLearningRecoveryOrgan


def test_organ_exists():

    organ = SelfLearningRecoveryOrgan()

    assert organ is not None
