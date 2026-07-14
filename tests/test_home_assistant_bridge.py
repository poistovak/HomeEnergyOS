from datetime import UTC, datetime

from heos.infrastructure.home_assistant.adapter import (
    HomeAssistantSnapshotAdapter,
)
from heos.infrastructure.home_assistant.executor import (
    DryRunHomeAssistantExecutor,
    HomeAssistantServiceCommand,
)
from heos.infrastructure.home_assistant.models import (
    EntityMap,
    HomeAssistantEntityState,
)


class FakeClient:
    def __init__(self, states: dict[str, str]) -> None:
        self.states = states
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def get_state(self, entity_id: str) -> HomeAssistantEntityState:
        return HomeAssistantEntityState(
            entity_id=entity_id,
            state=self.states[entity_id],
            last_updated=datetime.now(UTC),
        )

    def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, object],
    ) -> None:
        self.calls.append((domain, service, data))


def test_adapter_collects_energy_snapshot() -> None:
    client = FakeClient(
        {
            "sensor.pv": "5200",
            "sensor.house": "1400",
            "sensor.grid": "-3800",
            "sensor.ev_soc": "42",
            "binary_sensor.ev_connected": "on",
        }
    )
    adapter = HomeAssistantSnapshotAdapter(
        client,
        EntityMap(
            pv_power="sensor.pv",
            house_power="sensor.house",
            grid_power="sensor.grid",
            ev_soc="sensor.ev_soc",
            ev_connected="binary_sensor.ev_connected",
        ),
    )

    snapshot = adapter.collect()

    assert snapshot.pv_power_w == 5200
    assert snapshot.grid_export_w == 3800
    assert snapshot.ev_soc_percent == 42
    assert snapshot.ev_connected is True


def test_dry_run_executor_never_calls_real_client() -> None:
    executor = DryRunHomeAssistantExecutor()
    command = HomeAssistantServiceCommand(
        domain="switch",
        service="turn_on",
        data={"entity_id": "switch.wattpilot"},
        reason="Solar surplus available",
    )

    executor.execute(command)

    assert executor.commands == (command,)


def test_invalid_required_numeric_state_fails_safely() -> None:
    client = FakeClient(
        {
            "sensor.pv": "unknown",
            "sensor.house": "1400",
            "sensor.grid": "-3800",
        }
    )
    adapter = HomeAssistantSnapshotAdapter(
        client,
        EntityMap(
            pv_power="sensor.pv",
            house_power="sensor.house",
            grid_power="sensor.grid",
        ),
    )

    try:
        adapter.collect()
    except ValueError as error:
        assert "does not contain a numeric state" in str(error)
    else:
        raise AssertionError("Expected ValueError")
