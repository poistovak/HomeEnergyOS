"""Feature extraction from immutable HouseState snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from heos.house_state import HouseState


@dataclass(frozen=True, slots=True)
class EnergyFeatures:
    pv_w: float
    house_w: float
    grid_import_w: float
    grid_export_w: float
    ev_soc_percent: float | None
    ev_connected: bool | None
    charger_power_w: float
    self_sufficiency_percent: float
    source_confidence: float
    source_age_seconds: float
    cloud_risk_percent: float | None
    next_hour_price_eur_kwh: float | None
    reserve_power_w: float

    @property
    def net_surplus_w(self) -> float:
        return max(self.grid_export_w - self.reserve_power_w, 0.0)

    @property
    def has_ev_demand(self) -> bool:
        return (
            self.ev_connected is True
            and self.ev_soc_percent is not None
            and self.ev_soc_percent < 80.0
        )


class FeatureExtractor:
    """Convert HouseState into a stable, vendor-neutral feature vector."""

    def extract(self, state: HouseState) -> EnergyFeatures:
        twin = state.twin
        return EnergyFeatures(
            pv_w=twin.power.pv_w,
            house_w=twin.power.house_w,
            grid_import_w=twin.power.grid_import_w,
            grid_export_w=twin.power.grid_export_w,
            ev_soc_percent=twin.ev.soc_percent,
            ev_connected=twin.ev.connected,
            charger_power_w=twin.charger.power_w,
            self_sufficiency_percent=twin.power.self_sufficiency_percent,
            source_confidence=twin.power.quality.confidence,
            source_age_seconds=twin.power.quality.age_seconds,
            cloud_risk_percent=(
                state.predictions.expected_cloud_risk_percent
            ),
            next_hour_price_eur_kwh=(
                state.predictions.electricity_price_next_hour_eur_kwh
            ),
            reserve_power_w=state.policy.reserve_power_w,
        )
