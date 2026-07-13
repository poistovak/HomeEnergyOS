from heos.core import DeviceRecord, DeviceRegistry, Event, EventBus, HEOSKernel

def test_kernel_tick() -> None:
    kernel = HEOSKernel(
        state_provider=lambda: {"pv_w": 5000},
        decision_processor=lambda state: {"action": "charge_ev", "pv_w": state["pv_w"]},
    )
    result = kernel.tick()
    assert result.decision["action"] == "charge_ev"
    assert [event.topic for event in kernel.events.history] == [
        "kernel.tick.started", "state.updated", "decision.created", "kernel.tick.completed"
    ]

def test_registry_capability_lookup() -> None:
    registry = DeviceRegistry()
    registry.register(DeviceRecord(
        device_id="wattpilot",
        device_type="ev_charger",
        adapter="home_assistant",
        capabilities=frozenset({"set_current"}),
    ))
    assert registry.with_capability("set_current")[0].device_id == "wattpilot"

def test_event_bus() -> None:
    bus = EventBus()
    seen = []
    bus.subscribe("x", lambda event: seen.append(event.payload["v"]))
    bus.publish(Event("x", {"v": 1}))
    assert seen == [1]
