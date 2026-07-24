from heos.organs.plan_optimization.organ import PlanOptimizationOrgan


def test_organ_exists():

    organ = PlanOptimizationOrgan()

    assert organ is not None
