"""Confidence scoring for HEOS intelligence outputs."""

from __future__ import annotations

from dataclasses import dataclass

from .features import EnergyFeatures
from .forecast import EnergyForecast


@dataclass(frozen=True, slots=True)
class ConfidenceReport:
    score: float
    trustworthy: bool
    reasons: tuple[str, ...]


class ConfidenceScorer:
    """Combine data quality, freshness and forecast risk."""

    def score(
        self,
        features: EnergyFeatures,
        forecast: EnergyForecast,
        *,
        minimum_score: float = 0.80,
    ) -> ConfidenceReport:
        score = features.source_confidence
        reasons: list[str] = []

        if features.source_age_seconds > 60:
            score -= 0.35
            reasons.append("Source data is older than 60 seconds.")
        elif features.source_age_seconds > 30:
            score -= 0.10
            reasons.append("Source data is becoming stale.")

        if features.ev_connected is None:
            score -= 0.10
            reasons.append("EV connection state is unknown.")

        if features.ev_soc_percent is None:
            score -= 0.15
            reasons.append("EV SOC is unavailable.")

        if forecast.grid_risk > 0.50:
            score -= 0.10
            reasons.append("Forecast indicates elevated grid-import risk.")

        if features.cloud_risk_percent is None:
            score -= 0.05
            reasons.append("Cloud-risk input is unavailable.")

        score = min(max(score, 0.0), 1.0)

        if not reasons:
            reasons.append("Inputs are fresh, complete and internally consistent.")

        return ConfidenceReport(
            score=score,
            trustworthy=score >= minimum_score,
            reasons=tuple(reasons),
        )
