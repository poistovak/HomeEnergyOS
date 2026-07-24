from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from heos.feedback.models import ExperienceCandidate, OutcomeClassification, VersionStamp
from heos.memory import (
    HouseMemoryEngine,
    HouseMemoryRecord,
    InMemoryHouseMemoryRepository,
    JsonlHouseMemoryRepository,
    MemoryConflictError,
    MemoryFingerprint,
    MemoryNotFoundError,
    MemoryQuery,
    NumericRange,
    build_fingerprint,
    dumps_record,
    loads_record,
    numeric_similarity,
)

NOW = datetime(2026, 7, 15, 8, 0, tzinfo=UTC)


def versions(model: str = "model-1") -> VersionStamp:
    return VersionStamp(
        schema_version="feedback-1",
        forecast_version="forecast-1",
        model_version=model,
        policy_version="policy-1",
        compiler_version="compiler-1",
    )


def experience(
    record_id: str = "exp-1",
    *,
    features: dict[str, float] | None = None,
    targets: dict[str, float] | None = None,
    quality: float = 0.9,
    classification: OutcomeClassification = OutcomeClassification.EXCELLENT,
    created_at: datetime = NOW,
    model: str = "model-1",
) -> ExperienceCandidate:
    return ExperienceCandidate(
        record_id=record_id,
        decision_record_id=f"decision-{record_id}",
        outcome_record_id=f"outcome-{record_id}",
        comparison_record_id=f"comparison-{record_id}",
        created_at=created_at,
        features=features or {"pv_kw": 5.0, "load_kw": 2.0},
        targets=targets or {"grid_kw": 0.1},
        quality_score=quality,
        classification=classification,
        versions=versions(model),
        explanation=f"experience {record_id}",
    )


def remembered(
    record_id: str = "exp-1",
    *,
    repo: InMemoryHouseMemoryRepository | None = None,
    **kwargs: object,
) -> HouseMemoryRecord:
    active_repo = repo or InMemoryHouseMemoryRepository()
    engine = HouseMemoryEngine(active_repo)
    return engine.remember(experience(record_id, **kwargs), remembered_at=NOW)


def test_numeric_range_accepts_boundaries() -> None:
    value_range = NumericRange(1, 2)
    assert value_range.contains(1)
    assert value_range.contains(2)


def test_numeric_range_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="maximum"):
        NumericRange(2, 1)


def test_numeric_range_supports_open_bounds() -> None:
    assert NumericRange(minimum=2).contains(10)
    assert not NumericRange(maximum=2).contains(3)


def test_memory_fingerprint_validates_precision() -> None:
    with pytest.raises(ValueError, match="precision"):
        MemoryFingerprint("abc", (), 13)


def test_memory_record_is_frozen() -> None:
    record = remembered()
    with pytest.raises(FrozenInstanceError):
        record.record_id = "changed"  # type: ignore[misc]


def test_memory_record_freezes_feature_mapping() -> None:
    record = remembered()
    with pytest.raises(TypeError):
        record.features["pv_kw"] = 10  # type: ignore[index]


def test_memory_record_sorts_and_deduplicates_tags() -> None:
    engine = HouseMemoryEngine(InMemoryHouseMemoryRepository())
    record = engine.remember(
        experience(),
        remembered_at=NOW,
        tags=("winter", "solar", "winter"),
    )
    assert record.tags == ("solar", "winter")


def test_memory_record_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        replace(remembered(), remembered_at=datetime(2026, 7, 15))  # noqa: DTZ001


def test_memory_query_rejects_invalid_quality() -> None:
    with pytest.raises(ValueError, match="min_quality"):
        MemoryQuery(min_quality=1.1)


def test_memory_query_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="limit"):
        MemoryQuery(limit=0)


def test_memory_query_rejects_reversed_times() -> None:
    with pytest.raises(ValueError, match="occurred_until"):
        MemoryQuery(occurred_from=NOW, occurred_until=NOW - timedelta(seconds=1))


def test_fingerprint_is_order_independent() -> None:
    first = build_fingerprint(
        features={"b": 2, "a": 1},
        targets={"z": 3},
        classification=OutcomeClassification.EXCELLENT,
        versions=versions(),
    )
    second = build_fingerprint(
        features={"a": 1, "b": 2},
        targets={"z": 3},
        classification=OutcomeClassification.EXCELLENT,
        versions=versions(),
    )
    assert first == second


def test_fingerprint_respects_precision() -> None:
    first = build_fingerprint(
        features={"pv": 1.2344},
        targets={},
        classification=OutcomeClassification.ACCEPTABLE,
        versions=versions(),
        precision=3,
    )
    second = build_fingerprint(
        features={"pv": 1.23449},
        targets={},
        classification=OutcomeClassification.ACCEPTABLE,
        versions=versions(),
        precision=3,
    )
    assert first.digest == second.digest


def test_fingerprint_changes_with_version() -> None:
    first = build_fingerprint(
        features={"pv": 1},
        targets={},
        classification=OutcomeClassification.ACCEPTABLE,
        versions=versions("model-a"),
    )
    second = build_fingerprint(
        features={"pv": 1},
        targets={},
        classification=OutcomeClassification.ACCEPTABLE,
        versions=versions("model-b"),
    )
    assert first.digest != second.digest


def test_fingerprint_normalizes_negative_zero() -> None:
    first = build_fingerprint(
        features={"grid": -0.0},
        targets={},
        classification=OutcomeClassification.EXCELLENT,
        versions=versions(),
    )
    second = build_fingerprint(
        features={"grid": 0.0},
        targets={},
        classification=OutcomeClassification.EXCELLENT,
        versions=versions(),
    )
    assert first.digest == second.digest


def test_similarity_exact_match_is_one() -> None:
    result = numeric_similarity({"pv": 5, "load": 2}, {"pv": 5, "load": 2})
    assert result.score == 1.0
    assert result.overlap == 1.0


def test_similarity_is_symmetric() -> None:
    left = numeric_similarity({"pv": 5}, {"pv": 4})
    right = numeric_similarity({"pv": 4}, {"pv": 5})
    assert left == right


def test_similarity_penalizes_missing_dimensions() -> None:
    result = numeric_similarity({"pv": 5, "load": 2}, {"pv": 5})
    assert result.score == 0.5
    assert result.overlap == 0.5


def test_similarity_without_overlap_is_zero() -> None:
    result = numeric_similarity({"pv": 5}, {"load": 2})
    assert result.score == 0.0
    assert result.matched_dimensions == ()


def test_similarity_is_bounded() -> None:
    result = numeric_similarity({"pv": 1}, {"pv": 1000})
    assert 0.0 <= result.score <= 1.0


def test_in_memory_repository_append_and_get() -> None:
    repo = InMemoryHouseMemoryRepository()
    record = remembered(repo=repo)
    assert repo.get(record.record_id) == record


def test_in_memory_repository_missing_record() -> None:
    repo = InMemoryHouseMemoryRepository()
    with pytest.raises(MemoryNotFoundError):
        repo.get("missing")


def test_in_memory_repository_idempotent_append() -> None:
    repo = InMemoryHouseMemoryRepository()
    record = remembered(repo=repo)
    repo.append(record)
    assert repo.list_all() == (record,)


def test_in_memory_repository_rejects_changed_duplicate_id() -> None:
    repo = InMemoryHouseMemoryRepository()
    record = remembered(repo=repo)
    with pytest.raises(MemoryConflictError, match="record_id"):
        repo.append(replace(record, quality_score=0.1))


def test_in_memory_repository_rejects_changed_duplicate_source() -> None:
    repo = InMemoryHouseMemoryRepository()
    record = remembered(repo=repo)
    changed = replace(record, record_id="another-id", quality_score=0.1)
    with pytest.raises(MemoryConflictError, match="source_experience_id"):
        repo.append(changed)


def test_in_memory_repository_preserves_append_order() -> None:
    repo = InMemoryHouseMemoryRepository()
    engine = HouseMemoryEngine(repo)
    first = engine.remember(experience("exp-1"), remembered_at=NOW)
    second = engine.remember(experience("exp-2"), remembered_at=NOW)
    assert repo.list_all() == (first, second)


def test_serialization_round_trip() -> None:
    record = remembered()
    assert loads_record(dumps_record(record)) == record


def test_jsonl_repository_persists_records(tmp_path: Path) -> None:
    path = tmp_path / "memory.jsonl"
    repo = JsonlHouseMemoryRepository(path)
    record = remembered(repo=repo)
    reloaded = JsonlHouseMemoryRepository(path)
    assert reloaded.get(record.record_id) == record


def test_jsonl_repository_does_not_duplicate_idempotent_append(tmp_path: Path) -> None:
    path = tmp_path / "memory.jsonl"
    repo = JsonlHouseMemoryRepository(path)
    record = remembered(repo=repo)
    repo.append(record)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1


def test_jsonl_repository_reports_bad_line(tmp_path: Path) -> None:
    path = tmp_path / "memory.jsonl"
    path.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        JsonlHouseMemoryRepository(path)


def test_engine_remembers_experience_candidate() -> None:
    engine = HouseMemoryEngine(InMemoryHouseMemoryRepository())
    source = experience()
    record = engine.remember(source, remembered_at=NOW)
    assert record.source_experience_id == source.record_id
    assert record.features == source.features
    assert record.targets == source.targets


def test_engine_uses_experience_time_by_default() -> None:
    source = experience(created_at=NOW - timedelta(hours=2))
    record = HouseMemoryEngine(InMemoryHouseMemoryRepository()).remember(
        source,
        remembered_at=NOW,
    )
    assert record.occurred_at == source.created_at


def test_engine_accepts_explicit_occurrence_time() -> None:
    occurred_at = NOW - timedelta(days=1)
    record = HouseMemoryEngine(InMemoryHouseMemoryRepository()).remember(
        experience(),
        remembered_at=NOW,
        occurred_at=occurred_at,
    )
    assert record.occurred_at == occurred_at


def test_engine_remember_is_idempotent() -> None:
    engine = HouseMemoryEngine(InMemoryHouseMemoryRepository())
    source = experience()
    first = engine.remember(source, remembered_at=NOW)
    second = engine.remember(source, remembered_at=NOW)
    assert first is second


def test_engine_retry_keeps_original_remembered_time() -> None:
    engine = HouseMemoryEngine(InMemoryHouseMemoryRepository())
    source = experience()
    first = engine.remember(source, remembered_at=NOW)
    second = engine.remember(source, remembered_at=NOW + timedelta(minutes=5))
    assert second is first
    assert second.remembered_at == NOW


def test_engine_rejects_changed_retry() -> None:
    engine = HouseMemoryEngine(InMemoryHouseMemoryRepository())
    engine.remember(experience(), remembered_at=NOW)
    with pytest.raises(MemoryConflictError, match="different content"):
        engine.remember(
            experience(quality=0.2),
            remembered_at=NOW,
        )


def test_engine_remember_many() -> None:
    engine = HouseMemoryEngine(InMemoryHouseMemoryRepository())
    records = engine.remember_many(
        (experience("exp-1"), experience("exp-2")),
        remembered_at=NOW,
        tags=("batch",),
    )
    assert len(records) == 2
    assert all(record.tags == ("batch",) for record in records)


def populated_engine() -> HouseMemoryEngine:
    repo = InMemoryHouseMemoryRepository()
    engine = HouseMemoryEngine(repo)
    engine.remember(
        experience(
            "old",
            features={"pv_kw": 2.0, "load_kw": 2.5},
            targets={"grid_kw": 0.5},
            quality=0.6,
            classification=OutcomeClassification.DEGRADED,
            created_at=NOW - timedelta(days=2),
        ),
        remembered_at=NOW,
        tags=("winter", "cloudy"),
    )
    engine.remember(
        experience(
            "new",
            features={"pv_kw": 5.0, "load_kw": 2.0},
            targets={"grid_kw": 0.1},
            quality=0.95,
            classification=OutcomeClassification.EXCELLENT,
            created_at=NOW - timedelta(hours=1),
        ),
        remembered_at=NOW,
        tags=("summer", "solar"),
    )
    engine.remember(
        experience(
            "mid",
            features={"pv_kw": 4.5, "load_kw": 2.2},
            targets={"grid_kw": 0.2},
            quality=0.85,
            classification=OutcomeClassification.ACCEPTABLE,
            created_at=NOW - timedelta(days=1),
            model="model-2",
        ),
        remembered_at=NOW,
        tags=("summer", "solar"),
    )
    return engine


def test_recall_defaults_to_newest_first() -> None:
    records = populated_engine().recall()
    assert [record.source_experience_id for record in records] == ["new", "mid", "old"]


def test_recall_filters_feature_range() -> None:
    records = populated_engine().recall(
        MemoryQuery(feature_ranges={"pv_kw": NumericRange(4.8, 5.2)})
    )
    assert [record.source_experience_id for record in records] == ["new"]


def test_recall_filters_target_range() -> None:
    records = populated_engine().recall(
        MemoryQuery(target_ranges={"grid_kw": NumericRange(maximum=0.2)})
    )
    assert {record.source_experience_id for record in records} == {"new", "mid"}


def test_recall_filters_classification() -> None:
    records = populated_engine().recall(
        MemoryQuery(classifications=frozenset({OutcomeClassification.DEGRADED}))
    )
    assert [record.source_experience_id for record in records] == ["old"]


def test_recall_filters_all_tags() -> None:
    records = populated_engine().recall(
        MemoryQuery(tags_all=frozenset({"summer", "solar"}))
    )
    assert {record.source_experience_id for record in records} == {"new", "mid"}


def test_recall_filters_any_tag() -> None:
    records = populated_engine().recall(
        MemoryQuery(tags_any=frozenset({"cloudy", "missing"}))
    )
    assert [record.source_experience_id for record in records] == ["old"]


def test_recall_filters_quality() -> None:
    records = populated_engine().recall(MemoryQuery(min_quality=0.9))
    assert [record.source_experience_id for record in records] == ["new"]


def test_recall_filters_time_window() -> None:
    records = populated_engine().recall(
        MemoryQuery(occurred_from=NOW - timedelta(hours=2))
    )
    assert [record.source_experience_id for record in records] == ["new"]


def test_recall_filters_version() -> None:
    records = populated_engine().recall(MemoryQuery(model_version="model-2"))
    assert [record.source_experience_id for record in records] == ["mid"]


def test_recall_honors_limit() -> None:
    records = populated_engine().recall(MemoryQuery(limit=2))
    assert len(records) == 2


def test_recall_similar_ranks_best_match_first() -> None:
    matches = populated_engine().recall_similar({"pv_kw": 5.0, "load_kw": 2.0})
    assert matches[0].record.source_experience_id == "new"
    assert matches[0].similarity == 1.0


def test_recall_similar_filters_minimum_similarity() -> None:
    matches = populated_engine().recall_similar(
        {"pv_kw": 5.0, "load_kw": 2.0},
        min_similarity=0.95,
    )
    assert [match.record.source_experience_id for match in matches] == ["new"]


def test_recall_similar_filters_tags() -> None:
    matches = populated_engine().recall_similar(
        {"pv_kw": 2.0, "load_kw": 2.5},
        tags_all=("summer",),
    )
    assert all("summer" in match.record.tags for match in matches)


def test_recall_similar_rejects_empty_features() -> None:
    with pytest.raises(ValueError, match="features"):
        populated_engine().recall_similar({})


def test_recall_similar_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="limit"):
        populated_engine().recall_similar({"pv_kw": 1.0}, limit=0)


def test_summarize_calculates_means() -> None:
    engine = populated_engine()
    records = engine.recall(MemoryQuery(tags_all=frozenset({"summer"})))
    summary = engine.summarize(records, generated_at=NOW)
    assert summary.sample_count == 2
    assert summary.feature_means["pv_kw"] == pytest.approx(4.75)
    assert summary.target_means["grid_kw"] == pytest.approx(0.15)
    assert summary.mean_quality == pytest.approx(0.9)


def test_summarize_counts_classifications() -> None:
    engine = populated_engine()
    summary = engine.summarize(engine.recall(), generated_at=NOW)
    assert summary.classification_counts == {
        "acceptable": 1,
        "degraded": 1,
        "excellent": 1,
    }
    assert summary.dominant_classification == OutcomeClassification.ACCEPTABLE


def test_summarize_is_deterministic_for_member_set() -> None:
    engine = populated_engine()
    records = engine.recall()
    first = engine.summarize(records, generated_at=NOW)
    second = engine.summarize(reversed(records), generated_at=NOW)
    assert first.pattern_id == second.pattern_id


def test_summarize_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        populated_engine().summarize((), generated_at=NOW)
