from heos.organs.architecture_consistency.organ import ArchitectureConsistencyOrgan


def test_organ_exists():

    organ = ArchitectureConsistencyOrgan()

    assert organ is not None
