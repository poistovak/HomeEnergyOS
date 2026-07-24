from heos.organs.plan_evaluation.organ import PlanEvaluationOrgan


def test_organ_exists():

    organ = PlanEvaluationOrgan()

    assert organ is not None
