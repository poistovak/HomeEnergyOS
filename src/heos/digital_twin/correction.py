from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from heos.memory.models import PatternSummary

from .models import (
    CorrectionVector,
    TwinControl,
    TwinDisturbance,
    TwinParameters,
    TwinState,
)


@dataclass(frozen=True, slots=True)
class CorrectionContext:
    state: TwinState
    control: TwinControl
    disturbance: TwinDisturbance
    parameters: TwinParameters
    duration_hours: float


class ResidualCorrectionModel(Protocol):
    @property
    def version(self) -> str: ...

    def predict(self, context: CorrectionContext) -> CorrectionVector: ...


@dataclass(frozen=True, slots=True)
class NoResidualCorrection:
    version: str = "none"

    def predict(self, context: CorrectionContext) -> CorrectionVector:
        del context
        return CorrectionVector()


@dataclass(frozen=True, slots=True)
class FixedResidualCorrection:
    correction: CorrectionVector
    version: str = "fixed-1"

    def predict(self, context: CorrectionContext) -> CorrectionVector:
        del context
        return self.correction


@dataclass(frozen=True, slots=True)
class HouseMemoryPatternCorrection:
    pattern: PatternSummary
    max_temp_delta_c: float = 2.0
    max_power_delta_kw: float = 5.0
    quality_weighted: bool = True
    version: str = "house-memory-pattern-1"

    def __post_init__(self) -> None:
        if self.max_temp_delta_c < 0.0:
            raise ValueError("max_temp_delta_c must be non-negative")
        if self.max_power_delta_kw < 0.0:
            raise ValueError("max_power_delta_kw must be non-negative")
        if not str(self.version).strip():
            raise ValueError("version must not be empty")

    @staticmethod
    def _clamp(value: float, limit: float) -> float:
        return max(-limit, min(limit, float(value)))

    def predict(self, context: CorrectionContext) -> CorrectionVector:
        del context
        weight = self.pattern.mean_quality if self.quality_weighted else 1.0
        targets = self.pattern.target_means
        indoor = self._clamp(
            targets.get("indoor_temp_error_c", 0.0) * weight,
            self.max_temp_delta_c,
        )
        load = self._clamp(
            targets.get("base_load_error_kw", 0.0) * weight,
            self.max_power_delta_kw,
        )
        pv = self._clamp(
            targets.get("pv_error_kw", 0.0) * weight,
            self.max_power_delta_kw,
        )
        return CorrectionVector(
            indoor_temp_delta_c=indoor,
            base_load_delta_kw=load,
            pv_delta_kw=pv,
            source=self.pattern.pattern_id,
            explanation=(
                "Deterministic residual correction from M16 pattern "
                f"with {self.pattern.sample_count} samples."
            ),
        )
