from heos.organs.self_diagnostic.organ import SelfDiagnosticOrgan


def test_organ_exists():

    organ = SelfDiagnosticOrgan()

    assert organ is not None
