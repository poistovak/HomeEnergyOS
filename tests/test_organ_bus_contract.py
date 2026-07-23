from heos.nervous import OrganBus, OrganEvent


def test_organ_bus_publish():

    received = []

    def listener(event):
        received.append(event)

    bus = OrganBus()

    bus.subscribe(listener)

    event = OrganEvent(
        source="solar_optimizer",
        event="surplus_detected",
        data={"power": 4500},
    )

    bus.publish(event)

    assert len(received) == 1
    assert received[0].event == "surplus_detected"