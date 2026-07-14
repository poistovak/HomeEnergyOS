from datetime import UTC, datetime

from heos.infrastructure.home_assistant import (
    EntityMap,
    HomeAssistantEntityState,
    HomeAssistantSnapshotAdapter,
)


class DemoClient:
    def get_state(self, entity_id: str) -> HomeAssistantEntityState:
        values = {
            "sensor.fronius_pv_power": "6100",
            "sensor.fronius_house_power": "1450",
            "sensor.fronius_grid_power": "-4650",
            "sensor.omoda_battery": "42",
            "binary_sensor.omoda_connected": "on",
            "sensor.wattpilot_power": "0",
        }
        return HomeAssistantEntityState(
            entity_id=entity_id,
            state=values[entity_id],
            last_updated=datetime.now(UTC),
        )

    def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, object],
    ) -> None:
        raise RuntimeError("Demo client is read-only")


adapter = HomeAssistantSnapshotAdapter(
    DemoClient(),
    EntityMap(
        pv_power="sensor.fronius_pv_power",
        house_power="sensor.fronius_house_power",
        grid_power="sensor.fronius_grid_power",
        ev_soc="sensor.omoda_battery",
        ev_connected="binary_sensor.omoda_connected",
        charger_power="sensor.wattpilot_power",
    ),
)

snapshot = adapter.collect()
print(snapshot)
print("Solar surplus:", snapshot.solar_surplus_w, "W")
