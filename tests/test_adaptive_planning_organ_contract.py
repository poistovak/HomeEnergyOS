from heos.organs.adaptive_planning.organ import AdaptivePlanningOrgan


def test_organ_exists():

    organ = AdaptivePlanningOrgan()

    assert organ is not None
