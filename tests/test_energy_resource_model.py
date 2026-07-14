from heos.resources import (
    EnergyCarrier, EnergyFlow, EnergyResource, ResourceGraph,
    ResourceIdentity, ResourceKind
)

def make_resource(resource_id: str, name: str, kind: ResourceKind, *caps: str) -> EnergyResource:
    return EnergyResource(
        identity=ResourceIdentity(resource_id=resource_id, name=name, kind=kind),
        capabilities=frozenset(caps),
    )

def test_graph_models_energy_path() -> None:
    graph = ResourceGraph()
    solar = make_resource("producer.solar", "Solar Roof", ResourceKind.PRODUCER, "produce_energy")
    bus = make_resource("converter.house_bus", "House AC Bus", ResourceKind.CONVERTER, "transport_energy")
    ev = make_resource("storage.ev", "Omoda 9", ResourceKind.STORAGE, "store_energy")
    for item in (solar, bus, ev):
        graph.add_resource(item)
    graph.connect(EnergyFlow("producer.solar", "converter.house_bus", EnergyCarrier.ELECTRICITY_AC, 5000, 0.98))
    graph.connect(EnergyFlow("converter.house_bus", "storage.ev", EnergyCarrier.ELECTRICITY_AC, 2300, 0.95))
    assert graph.has_path("producer.solar", "storage.ev") is True
    assert graph.outgoing("producer.solar") == (bus,)

def test_flow_calculates_losses() -> None:
    flow = EnergyFlow("producer.solar", "storage.ev", EnergyCarrier.ELECTRICITY_AC, 3000, 0.90)
    assert flow.delivered_power_w == 2700
    assert flow.losses_w == 300
