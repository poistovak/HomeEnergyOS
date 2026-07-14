"""Short-horizon deterministic energy forecast."""

from __future__ import annotations

from dataclasses import dataclass

from .features import EnergyFeatures
from .trend import Trend, TrendDirection


@dataclass(frozen=True, slots=True)
class EnergyForecast:
    pv_15m_w: float
    house_15m_w: float
    surplus_15m_w: float
    grid_risk: float
    explanation: tuple[str, ...]


class ForecastEngine:
    """Project the next 15 minutes from features and recent trends."""

    def forecast(
        self,
        features: EnergyFeatures,
        *,
        pv_trend: Trend | None = None,
        house_trend: Trend | None = None,
    ) -> EnergyForecast:
        pv_delta = 0.0 if pv_trend is None else pv_trend.slope_per_step
        house_delta = (
            0.0 if house_trend is None else house_trend.slope_per_step
        )

        projected_pv = max(features.pv_w + pv_delta, 0.0)
        projected_house = max(features.house_w + house_delta, 0.0)

        reasons: list[str] = []

        cloud_risk = features.cloud_risk_percent
        if cloud_risk is not None:
            attenuation = min(max(cloud_risk / 100.0, 0.0), 1.0)
            projected_pv *= 1.0 - (0.45 * attenuation)
            reasons.append(
                f"Cloud risk {cloud_risk:.0f}% reduced projected PV."
            )

        if (
            pv_trend is not None
            and pv_trend.direction is TrendDirection.FALLING
        ):
            reasons.append("Recent PV production is falling.")

        if (
            house_trend is not None
            and house_trend.direction is TrendDirection.RISING
        ):
            reasons.append("Recent household demand is rising.")

        projected_surplus = max(
            projected_pv
            - projected_house
            - features.reserve_power_w,
            0.0,
        )

        projected_deficit = max(
            projected_house + features.reserve_power_w - projected_pv,
            0.0,
        )
        denominator = max(projected_house + features.reserve_power_w, 1.0)
        grid_risk = min(projected_deficit / denominator, 1.0)

        if not reasons:
            reasons.append("Forecast based on current stable state.")

        return EnergyForecast(
            pv_15m_w=projected_pv,
            house_15m_w=projected_house,
            surplus_15m_w=projected_surplus,
            grid_risk=grid_risk,
            explanation=tuple(reasons),
        )
