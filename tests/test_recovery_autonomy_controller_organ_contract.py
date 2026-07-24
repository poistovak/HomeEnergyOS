from heos.organs.recovery_autonomy_controller.organ import RecoveryAutonomyControllerOrgan


def test_organ_exists():

    organ = RecoveryAutonomyControllerOrgan()

    assert organ is not None
