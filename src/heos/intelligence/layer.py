"""Facade combining feature extraction, forecasting and confidence."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from heos.house_state import HouseState

from .confidence import ConfidenceReport, ConfidenceScorer
from .features import EnergyFeatures, FeatureExtractor
from .forecast import EnergyForecast, ForecastEngine
from .trend import Trend, TrendEstimator


@dataclass(frozen=True, slots=True)
class IntelligenceResult:
    features: EnergyFeatures
    forecast: EnergyForecast
    confidence: ConfidenceReport
    pv_trend: Trend
    house_trend: Trend

    @property
    def ready_for_decision(self) -> bool:
        return self.confidence.trustworthy


class IntelligenceLayer:
    """Produce decision-ready intelligence from HouseState and history."""

    def __init__(self) -> None:
        self._features = FeatureExtractor()
        self._trends = TrendEstimator()
        self._forecast = ForecastEngine()
        self._confidence = ConfidenceScorer()

    def analyze(
        self,
        state: HouseState,
        *,
        pv_history_w: Sequence[float] = (),
        house_history_w: Sequence[float] = (),
    ) -> IntelligenceResult:
        features = self._features.extract(state)
        pv_values = tuple(pv_history_w) or (features.pv_w,)
        house_values = tuple(house_history_w) or (features.house_w,)
        pv_trend = self._trends.estimate(pv_values)
        house_trend = self._trends.estimate(house_values)
        forecast = self._forecast.forecast(
            features,
            pv_trend=pv_trend,
            house_trend=house_trend,
        )
        confidence = self._confidence.score(features, forecast)

        return IntelligenceResult(
            features=features,
            forecast=forecast,
            confidence=confidence,
            pv_trend=pv_trend,
            house_trend=house_trend,
        )
