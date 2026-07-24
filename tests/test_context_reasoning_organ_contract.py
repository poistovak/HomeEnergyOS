from heos.organs.context_reasoning.organ import ContextReasoningOrgan


def test_organ_exists():

    organ = ContextReasoningOrgan()

    assert organ is not None
