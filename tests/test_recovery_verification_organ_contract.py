from heos.organs.recovery_verification.organ import RecoveryVerificationOrgan


def test_organ_exists():

    organ = RecoveryVerificationOrgan()

    assert organ is not None
