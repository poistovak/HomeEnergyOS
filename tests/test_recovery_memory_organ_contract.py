from heos.organs.recovery_memory.organ import RecoveryMemoryOrgan


def test_organ_exists():

    organ = RecoveryMemoryOrgan()

    assert organ is not None
