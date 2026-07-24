from heos.organs.plan_selection.organ import PlanSelectionOrgan


def test_organ_exists():

    organ = PlanSelectionOrgan()

    assert organ is not None
