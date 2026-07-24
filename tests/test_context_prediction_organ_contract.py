from heos.organs.context_prediction.organ import ContextPredictionOrgan


def test_organ_exists():

    organ = ContextPredictionOrgan()

    assert organ is not None
