from heos.organs.recovery_pattern_recognition.organ import RecoveryPatternRecognitionOrgan


def test_organ_exists():

    organ = RecoveryPatternRecognitionOrgan()

    assert organ is not None
