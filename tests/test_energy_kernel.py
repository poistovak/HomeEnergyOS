from dataclasses import dataclass

from heos.kernel import EnergyKernel, KernelHealth
from heos.resources import (
    EnergyCarrier,
    EnergyFlow,
    EnergyResource,
    ResourceHealth,
    ResourceIdentity,
    ResourceKind,
    ResourceState,
)


@dataclass(frozen=True, slots=True)
class PowerState(ResourceState):
    power_w: float = 0.0


def resource(
    resource_id: str,
    name: str,
    kind: ResourceKind,
) -> EnergyResource:
    return EnergyResource(
        identity=ResourceIdentity(
            resource_id=resource_id,
            name=name,
            kind=kind,
        )
    )


def test_kernel_calculates_balanced_home() -> None:
    kernel = EnergyKernel()

    solar = resource(
        "producer.solar",
        "Solar Roof",
        ResourceKind.PRODUCER,
    )
    house = resource(
        "consumer.house",
        "House Loads",
        ResourceKind.CONSUMER,
    )
    ev = resource(
        "storage.ev",
        "Omoda 9",
        ResourceKind.STORAGE,
    )

    for item in (solar, house, ev):
        kernel.register(item)

    kernel.observe_many(
        (
            PowerState(
                resource_id="producer.solar",
                health=ResourceHealth.ONLINE,
                power_w=5000,
            ),
            PowerState(
                resource_id="consumer.house",
                health=ResourceHealth.ONLINE,
                power_w=2000,
            ),
            PowerState(
                resource_id="storage.ev",
                health=ResourceHealth.ONLINE,
                power_w=-3000,
            ),
        )
    )

    snapshot = kernel.snapshot()

    assert snapshot.health is KernelHealth.READY
    assert snapshot.balance.production_w == 5000
    assert snapshot.balance.consumption_w == 2000
    assert snapshot.balance.storage_charge_w == 3000
    assert snapshot.balance.balanced is True


def test_kernel_is_degraded_when_state_is_missing() -> None:
    kernel = EnergyKernel()
    kernel.register(
        resource(
            "producer.solar",
            "Solar Roof",
            ResourceKind.PRODUCER,
        )
    )

    snapshot = kernel.snapshot()

    assert snapshot.health is KernelHealth.DEGRADED
    assert snapshot.issues[0].code == "MISSING_STATE"


def test_kernel_is_blocked_by_failed_resource() -> None:
    kernel = EnergyKernel()
    solar = resource(
        "producer.solar",
        "Solar Roof",
        ResourceKind.PRODUCER,
    )
    kernel.register(solar)
    kernel.observe(
        PowerState(
            resource_id="producer.solar",
            health=ResourceHealth.FAILED,
            power_w=0,
        )
    )

    assert kernel.snapshot().health is KernelHealth.BLOCKED


def test_kernel_checks_energy_route() -> None:
    kernel = EnergyKernel()

    solar = resource(
        "producer.solar",
        "Solar Roof",
        ResourceKind.PRODUCER,
    )
    bus = resource(
        "converter.house_bus",
        "House AC Bus",
        ResourceKind.CONVERTER,
    )
    ev = resource(
        "storage.ev",
        "Omoda 9",
        ResourceKind.STORAGE,
    )

    for item in (solar, bus, ev):
        kernel.register(item)

    kernel.graph.connect(
        EnergyFlow(
            source_id=solar.resource_id,
            destination_id=bus.resource_id,
            carrier=EnergyCarrier.ELECTRICITY_AC,
            power_w=5000,
        )
    )
    kernel.graph.connect(
        EnergyFlow(
            source_id=bus.resource_id,
            destination_id=ev.resource_id,
            carrier=EnergyCarrier.ELECTRICITY_AC,
            power_w=2300,
        )
    )

    assert kernel.can_route("producer.solar", "storage.ev") is True
