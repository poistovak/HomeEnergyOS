from heos.organs.organ_registry.organ import OrganRegistryOrgan


def test_organ_exists():

    organ = OrganRegistryOrgan()

    assert organ is not None
