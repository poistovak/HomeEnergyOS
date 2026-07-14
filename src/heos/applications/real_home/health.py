from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from heos.infrastructure.home_assistant.models import RawEnergySnapshot


@dataclass(frozen=True, slots=True)
class SnapshotHealth:
    healthy: bool
    reasons: tuple[str, ...]
    checked_at: datetime


class SnapshotHealthChecker:
    def evaluate(self, snapshot: RawEnergySnapshot) -> SnapshotHealth:
        reasons: list[str] = []

        if snapshot.pv_power_w < 0:
            reasons.append("PV power cannot be negative.")

        if snapshot.house_power_w < 0:
            reasons.append("House power cannot be negative.")

        if snapshot.ev_soc_percent is not None and not 0 <= snapshot.ev_soc_percent <= 100:
            reasons.append("EV SOC is outside 0..100%.")

        if snapshot.charger_current_a is not None and snapshot.charger_current_a < 0:
            reasons.append("Charger current cannot be negative.")

        return SnapshotHealth(
            healthy=not reasons,
            reasons=tuple(reasons) or ("Snapshot passed basic validation.",),
            checked_at=datetime.now(UTC),
        )
