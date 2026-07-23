from heos.organs.experience_ranking.organ import ExperienceRankingOrgan


def test_organ_exists():

    organ = ExperienceRankingOrgan()

    assert organ is not None
