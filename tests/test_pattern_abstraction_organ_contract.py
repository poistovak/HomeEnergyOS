from heos.organs.pattern_abstraction.organ import PatternAbstractionOrgan


def test_organ_exists():

    organ = PatternAbstractionOrgan()

    assert organ is not None
