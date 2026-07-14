"""Read-only Home Assistant snapshot adapter."""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime

from .client import HomeAssistantClient
from .models import EntityMap, RawEnergySnapshot


class HomeAssistantSnapshotAdapter:
    """Collect one consistent energy snapshot from mapped HA entities."""

    def __init__(
        self,
        client: HomeAssistantClient,
        entities: EntityMap,
    ) -> None:
        self._client = client
        self._entities = entities

    def collect(self) -> RawEnergySnapshot:
        pv = self._required_float(self._entities.pv_power)
        house = self._required_float(self._entities.house_power)
        grid = self._required_float(self._entities.grid_power)

        return RawEnergySnapshot(
            pv_power_w=pv,
            house_power_w=house,
            grid_power_w=grid,
            ev_soc_percent=self._optional_float(self._entities.ev_soc),
            ev_connected=self._optional_bool(self._entities.ev_connected),
            charger_power_w=self._optional_float(
                self._entities.charger_power
            ),
            charger_current_a=self._optional_float(
                self._entities.charger_current
            ),
            charger_enabled=self._optional_bool(
                self._entities.charger_enabled
            ),
            outdoor_temperature_c=self._optional_float(
                self._entities.outdoor_temperature
            ),
            electricity_price_eur_kwh=self._optional_float(
                self._entities.electricity_price
            ),
            collected_at=datetime.now(UTC),
            source_entities={
                item.name: entity_id
                for item in fields(self._entities)
                if (entity_id := getattr(self._entities, item.name)) is not None
            },
        )

    def _required_float(self, entity_id: str) -> float:
        value = self._client.get_state(entity_id).as_float()
        if value is None:
            raise ValueError(
                f"Entity {entity_id!r} does not contain a numeric state"
            )
        return value

    def _optional_float(self, entity_id: str | None) -> float | None:
        if entity_id is None:
            return None
        return self._client.get_state(entity_id).as_float()

    def _optional_bool(self, entity_id: str | None) -> bool | None:
        if entity_id is None:
            return None
        return self._client.get_state(entity_id).as_bool()
