from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime
from statistics import fmean
from typing import Iterable, Mapping
from uuid import NAMESPACE_URL, uuid5

from heos.feedback.models import ExperienceCandidate, OutcomeClassification

from .fingerprint import build_fingerprint, numeric_similarity
from .models import (
    HouseMemoryRecord,
    MemoryMatch,
    MemoryQuery,
    PatternSummary,
)
from .repository import HouseMemoryRepository, MemoryConflictError


class HouseMemoryEngine:
    def __init__(
        self,
        repository: HouseMemoryRepository,
        *,
        fingerprint_precision: int = 3,
    ) -> None:
        if fingerprint_precision < 0 or fingerprint_precision > 12:
            raise ValueError("fingerprint_precision must be between 0 and 12")
        self._repository = repository
        self._fingerprint_precision = fingerprint_precision

    def remember(
        self,
        experience: ExperienceCandidate,
        *,
        remembered_at: datetime,
        occurred_at: datetime | None = None,
        tags: Iterable[str] = (),
    ) -> HouseMemoryRecord:
        existing = self._repository.get_by_source(experience.record_id)
        fingerprint = build_fingerprint(
            features=experience.features,
            targets=experience.targets,
            classification=experience.classification,
            versions=experience.versions,
            precision=self._fingerprint_precision,
        )
        identifier = uuid5(
            NAMESPACE_URL,
            f"heos-house-memory:{experience.record_id}:{fingerprint.digest}",
        )
        record = HouseMemoryRecord(
            record_id=str(identifier),
            source_experience_id=experience.record_id,
            remembered_at=remembered_at,
            occurred_at=occurred_at or experience.created_at,
            features=experience.features,
            targets=experience.targets,
            quality_score=experience.quality_score,
            classification=experience.classification,
            versions=experience.versions,
            explanation=experience.explanation,
            fingerprint=fingerprint,
            tags=tuple(tags),
        )
        if existing is not None:
            retry_record = replace(record, remembered_at=existing.remembered_at)
            if existing == retry_record:
                return existing
            raise MemoryConflictError(
                f"experience already remembered with different content: {experience.record_id}"
            )
        self._repository.append(record)
        return record

    def remember_many(
        self,
        experiences: Iterable[ExperienceCandidate],
        *,
        remembered_at: datetime,
        tags: Iterable[str] = (),
    ) -> tuple[HouseMemoryRecord, ...]:
        frozen_tags = tuple(tags)
        return tuple(
            self.remember(
                experience,
                remembered_at=remembered_at,
                tags=frozen_tags,
            )
            for experience in experiences
        )

    def recall(self, query: MemoryQuery | None = None) -> tuple[HouseMemoryRecord, ...]:
        active_query = query or MemoryQuery()
        records = [
            record
            for record in self._repository.list_all()
            if self._matches(record, active_query)
        ]
        records.sort(key=lambda item: (item.occurred_at, item.record_id), reverse=True)
        if active_query.limit is not None:
            records = records[: active_query.limit]
        return tuple(records)

    def recall_similar(
        self,
        features: Mapping[str, float],
        *,
        limit: int = 10,
        min_similarity: float = 0.0,
        min_quality: float = 0.0,
        tags_all: Iterable[str] = (),
    ) -> tuple[MemoryMatch, ...]:
        if not features:
            raise ValueError("features must not be empty")
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be between 0 and 1")
        query = MemoryQuery(
            tags_all=frozenset(tags_all),
            min_quality=min_quality,
        )
        matches: list[MemoryMatch] = []
        for record in self.recall(query):
            result = numeric_similarity(features, record.features)
            if result.score < min_similarity:
                continue
            matches.append(
                MemoryMatch(
                    record=record,
                    similarity=result.score,
                    overlap=result.overlap,
                    matched_dimensions=result.matched_dimensions,
                )
            )
        matches.sort(
            key=lambda item: (
                item.similarity,
                item.record.quality_score,
                item.record.occurred_at,
                item.record.record_id,
            ),
            reverse=True,
        )
        return tuple(matches[:limit])

    def summarize(
        self,
        records: Iterable[HouseMemoryRecord],
        *,
        generated_at: datetime,
    ) -> PatternSummary:
        members = tuple(records)
        if not members:
            raise ValueError("records must not be empty")

        feature_values: dict[str, list[float]] = defaultdict(list)
        target_values: dict[str, list[float]] = defaultdict(list)
        classifications = Counter(record.classification.value for record in members)
        for record in members:
            for key, value in record.features.items():
                feature_values[key].append(value)
            for key, value in record.targets.items():
                target_values[key].append(value)

        feature_means = {
            key: fmean(values)
            for key, values in sorted(feature_values.items())
        }
        target_means = {
            key: fmean(values)
            for key, values in sorted(target_values.items())
        }
        dominant_value = sorted(
            classifications.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]
        member_ids = tuple(sorted(record.record_id for record in members))
        identifier = uuid5(
            NAMESPACE_URL,
            "heos-house-pattern:" + ":".join(member_ids),
        )
        return PatternSummary(
            pattern_id=str(identifier),
            generated_at=generated_at,
            member_ids=member_ids,
            sample_count=len(members),
            feature_means=feature_means,
            target_means=target_means,
            mean_quality=fmean(record.quality_score for record in members),
            classification_counts=dict(classifications),
            dominant_classification=OutcomeClassification(dominant_value),
        )

    @staticmethod
    def _matches(record: HouseMemoryRecord, query: MemoryQuery) -> bool:
        if record.quality_score < query.min_quality:
            return False
        if query.classifications and record.classification not in query.classifications:
            return False
        record_tags = set(record.tags)
        if query.tags_all and not query.tags_all.issubset(record_tags):
            return False
        if query.tags_any and not query.tags_any.intersection(record_tags):
            return False
        if query.occurred_from is not None and record.occurred_at < query.occurred_from:
            return False
        if query.occurred_until is not None and record.occurred_at > query.occurred_until:
            return False
        for key, numeric_range in query.feature_ranges.items():
            if key not in record.features or not numeric_range.contains(record.features[key]):
                return False
        for key, numeric_range in query.target_ranges.items():
            if key not in record.targets or not numeric_range.contains(record.targets[key]):
                return False
        versions = record.versions
        for name in (
            "schema_version",
            "forecast_version",
            "model_version",
            "policy_version",
            "compiler_version",
        ):
            expected = getattr(query, name)
            if expected is not None and getattr(versions, name) != expected:
                return False
        return True
