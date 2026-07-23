from heos.organs.pattern_transfer.organ import PatternTransferOrgan


def test_organ_exists():

    organ = PatternTransferOrgan()

    assert organ is not None
