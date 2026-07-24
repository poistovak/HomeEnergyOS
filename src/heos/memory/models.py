from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

from heos.feedback.models import OutcomeClassification, VersionStamp


def _require_text(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _freeze_float_mapping(values: Mapping[str, float]) -> Mapping[str, float]:
    normalized = {
        _require_text(str(key), "mapping key"): float(value)
        for key, value in values.items()
    }
    return MappingProxyType(dict(sorted(normalized.items())))


def _freeze_int_mapping(values: Mapping[str, int]) -> Mapping[str, int]:
    normalized = {
        _require_text(str(key), "mapping key"): int(value)
        for key, value in values.items()
    }
    return MappingProxyType(dict(sorted(normalized.items())))


class MemoryKind(StrEnum):
    EXPERIENCE = "experience"


@dataclass(frozen=True, slots=True)
class NumericRange:
    minimum: float | None = None
    maximum: float | None = None

    def __post_init__(self) -> None:
        if self.minimum is not None:
            object.__setattr__(self, "minimum", float(self.minimum))
        if self.maximum is not None:
            object.__setattr__(self, "maximum", float(self.maximum))
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.maximum < self.minimum
        ):
            raise ValueError("maximum must be greater than or equal to minimum")

    def contains(self, value: float) -> bool:
        value = float(value)
        if self.minimum is not None and value < self.minimum:
            return False
        return not (self.maximum is not None and value > self.maximum)


@dataclass(frozen=True, slots=True)
class MemoryFingerprint:
    digest: str
    dimensions: tuple[str, ...]
    precision: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "digest", _require_text(self.digest, "digest"))
        object.__setattr__(self, "dimensions", tuple(sorted(str(item) for item in self.dimensions)))
        if self.precision < 0 or self.precision > 12:
            raise ValueError("precision must be between 0 and 12")


@dataclass(frozen=True, slots=True)
class HouseMemoryRecord:
    record_id: str
    source_experience_id: str
    remembered_at: datetime
    occurred_at: datetime
    features: Mapping[str, float]
    targets: Mapping[str, float]
    quality_score: float
    classification: OutcomeClassification
    versions: VersionStamp
    explanation: str
    fingerprint: MemoryFingerprint
    tags: tuple[str, ...] = ()
    kind: MemoryKind = MemoryKind.EXPERIENCE

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _require_text(self.record_id, "record_id"))
        object.__setattr__(
            self,
            "source_experience_id",
            _require_text(self.source_experience_id, "source_experience_id"),
        )
        object.__setattr__(
            self,
            "remembered_at",
            _require_aware(self.remembered_at, "remembered_at"),
        )
        object.__setattr__(
            self,
            "occurred_at",
            _require_aware(self.occurred_at, "occurred_at"),
        )
        object.__setattr__(self, "features", _freeze_float_mapping(self.features))
        object.__setattr__(self, "targets", _freeze_float_mapping(self.targets))
        quality = float(self.quality_score)
        if not 0.0 <= quality <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")
        object.__setattr__(self, "quality_score", quality)
        object.__setattr__(
            self,
            "explanation",
            _require_text(self.explanation, "explanation"),
        )
        normalized_tags = tuple(sorted({_require_text(tag, "tag") for tag in self.tags}))
        object.__setattr__(self, "tags", normalized_tags)


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    feature_ranges: Mapping[str, NumericRange] = field(default_factory=dict)
    target_ranges: Mapping[str, NumericRange] = field(default_factory=dict)
    classifications: frozenset[OutcomeClassification] = frozenset()
    tags_all: frozenset[str] = frozenset()
    tags_any: frozenset[str] = frozenset()
    min_quality: float = 0.0
    occurred_from: datetime | None = None
    occurred_until: datetime | None = None
    schema_version: str | None = None
    forecast_version: str | None = None
    model_version: str | None = None
    policy_version: str | None = None
    compiler_version: str | None = None
    limit: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feature_ranges",
            MappingProxyType(dict(sorted(self.feature_ranges.items()))),
        )
        object.__setattr__(
            self,
            "target_ranges",
            MappingProxyType(dict(sorted(self.target_ranges.items()))),
        )
        object.__setattr__(self, "classifications", frozenset(self.classifications))
        object.__setattr__(
            self,
            "tags_all",
            frozenset(_require_text(tag, "tag") for tag in self.tags_all),
        )
        object.__setattr__(
            self,
            "tags_any",
            frozenset(_require_text(tag, "tag") for tag in self.tags_any),
        )
        quality = float(self.min_quality)
        if not 0.0 <= quality <= 1.0:
            raise ValueError("min_quality must be between 0 and 1")
        object.__setattr__(self, "min_quality", quality)
        if self.occurred_from is not None:
            _require_aware(self.occurred_from, "occurred_from")
        if self.occurred_until is not None:
            _require_aware(self.occurred_until, "occurred_until")
        if (
            self.occurred_from is not None
            and self.occurred_until is not None
            and self.occurred_until < self.occurred_from
        ):
            raise ValueError("occurred_until must not be before occurred_from")
        for name in (
            "schema_version",
            "forecast_version",
            "model_version",
            "policy_version",
            "compiler_version",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _require_text(value, name))
        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit must be greater than zero")


@dataclass(frozen=True, slots=True)
class MemoryMatch:
    record: HouseMemoryRecord
    similarity: float
    overlap: float
    matched_dimensions: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("similarity", "overlap"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
            object.__setattr__(self, name, value)
        object.__setattr__(
            self,
            "matched_dimensions",
            tuple(sorted(str(item) for item in self.matched_dimensions)),
        )


@dataclass(frozen=True, slots=True)
class PatternSummary:
    pattern_id: str
    generated_at: datetime
    member_ids: tuple[str, ...]
    sample_count: int
    feature_means: Mapping[str, float]
    target_means: Mapping[str, float]
    mean_quality: float
    classification_counts: Mapping[str, int]
    dominant_classification: OutcomeClassification

    def __post_init__(self) -> None:
        object.__setattr__(self, "pattern_id", _require_text(self.pattern_id, "pattern_id"))
        object.__setattr__(
            self,
            "generated_at",
            _require_aware(self.generated_at, "generated_at"),
        )
        member_ids = tuple(sorted(_require_text(item, "member_id") for item in self.member_ids))
        if not member_ids:
            raise ValueError("member_ids must not be empty")
        object.__setattr__(self, "member_ids", member_ids)
        if self.sample_count != len(member_ids):
            raise ValueError("sample_count must equal the number of member_ids")
        object.__setattr__(self, "feature_means", _freeze_float_mapping(self.feature_means))
        object.__setattr__(self, "target_means", _freeze_float_mapping(self.target_means))
        quality = float(self.mean_quality)
        if not 0.0 <= quality <= 1.0:
            raise ValueError("mean_quality must be between 0 and 1")
        object.__setattr__(self, "mean_quality", quality)
        counts = _freeze_int_mapping(self.classification_counts)
        if sum(counts.values()) != self.sample_count:
            raise ValueError("classification_counts must add up to sample_count")
        object.__setattr__(self, "classification_counts", counts)
