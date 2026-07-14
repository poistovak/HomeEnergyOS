"""Port implemented by any Home Assistant transport."""

from __future__ import annotations

from typing import Protocol

from .models import HomeAssistantEntityState


class HomeAssistantClient(Protocol):
    """Minimal client contract required by the HEOS bridge."""

    def get_state(self, entity_id: str) -> HomeAssistantEntityState:
        """Read one Home Assistant entity."""

    def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, object],
    ) -> None:
        """Call one Home Assistant service."""
