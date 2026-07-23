from heos.organs.experience_retrieval.organ import ExperienceRetrievalOrgan


def test_organ_exists():

    organ = ExperienceRetrievalOrgan()

    assert organ is not None
