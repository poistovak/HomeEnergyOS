from heos.organs.reflex_memory.organ import ReflexMemoryOrgan


def test_organ_exists():

    organ = ReflexMemoryOrgan()

    assert organ is not None
