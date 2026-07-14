from __future__ import annotations

from dataclasses import dataclass

from heos.infrastructure.home_assistant.adapter import HomeAssistantSnapshotAdapter
from heos.infrastructure.home_assistant.models import RawEnergySnapshot

from .health import SnapshotHealth, SnapshotHealthChecker


@dataclass(frozen=True, slots=True)
class RealHomeCycle:
    snapshot: RawEnergySnapshot
    health: SnapshotHealth


class RealHomeReadOnlyRuntime:
    """One read-only cycle against the user's real Home Assistant data."""

    def __init__(
        self,
        adapter: HomeAssistantSnapshotAdapter,
        health_checker: SnapshotHealthChecker | None = None,
    ) -> None:
        self._adapter = adapter
        self._health = health_checker or SnapshotHealthChecker()

    def run_once(self) -> RealHomeCycle:
        snapshot = self._adapter.collect()
        health = self._health.evaluate(snapshot)
        return RealHomeCycle(snapshot=snapshot, health=health)
