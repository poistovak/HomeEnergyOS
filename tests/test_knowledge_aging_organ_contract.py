from heos.organs.knowledge_aging.organ import KnowledgeAgingOrgan


def test_organ_exists():

    organ = KnowledgeAgingOrgan()

    assert organ is not None
