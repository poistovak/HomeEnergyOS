from heos.capabilities import CapabilityRegistry


class Dummy:
    pass


def test_register():
    registry = CapabilityRegistry()

    dummy = Dummy()

    registry.register(Dummy, dummy)

    assert registry.has(Dummy)
    assert registry.get(Dummy) is dummy