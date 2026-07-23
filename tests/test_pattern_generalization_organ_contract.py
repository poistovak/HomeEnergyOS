from heos.organs.pattern_generalization.organ import PatternGeneralizationOrgan


def test_organ_exists():

    organ = PatternGeneralizationOrgan()

    assert organ is not None
