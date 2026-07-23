from heos.organs.experience_synthesis.organ import ExperienceSynthesisOrgan


def test_organ_exists():

    organ = ExperienceSynthesisOrgan()

    assert organ is not None
