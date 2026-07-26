import pytest

from heos.result_verification.weighted_evidence import (
    Evidence,
    WeightedEvidenceEngine,
)


def test_identical_successful_experience_gives_full_confidence():
    engine = WeightedEvidenceEngine()

    result = engine.evaluate(
        [
            Evidence(
                similarity=1.0,
                success=True,
            )
        ]
    )

    assert result.confidence == 1.0
    assert result.samples == 1


def test_identical_failed_experience_gives_zero_confidence():
    engine = WeightedEvidenceEngine()

    result = engine.evaluate(
        [
            Evidence(
                similarity=1.0,
                success=False,
            )
        ]
    )

    assert result.confidence == 0.0


def test_more_similar_experience_has_greater_influence():
    engine = WeightedEvidenceEngine()

    result = engine.evaluate(
        [
            Evidence(
                similarity=0.9,
                success=True,
            ),
            Evidence(
                similarity=0.1,
                success=False,
            ),
        ]
    )

    assert result.confidence == pytest.approx(0.9)


def test_failed_high_similarity_experience_reduces_confidence():
    engine = WeightedEvidenceEngine()

    result = engine.evaluate(
        [
            Evidence(
                similarity=0.2,
                success=True,
            ),
            Evidence(
                similarity=0.8,
                success=False,
            ),
        ]
    )

    assert result.confidence == pytest.approx(0.2)


def test_multiple_evidence_samples_are_combined():
    engine = WeightedEvidenceEngine()

    result = engine.evaluate(
        [
            Evidence(0.9, True),
            Evidence(0.8, True),
            Evidence(0.7, False),
        ]
    )

    expected = (0.9 + 0.8) / (0.9 + 0.8 + 0.7)

    assert result.confidence == pytest.approx(expected)
    assert result.samples == 3


def test_zero_similarity_evidence_has_no_influence():
    engine = WeightedEvidenceEngine()

    result = engine.evaluate(
        [
            Evidence(1.0, True),
            Evidence(0.0, False),
        ]
    )

    assert result.confidence == 1.0


def test_all_zero_similarity_returns_zero_confidence():
    engine = WeightedEvidenceEngine()

    result = engine.evaluate(
        [
            Evidence(0.0, True),
            Evidence(0.0, True),
        ]
    )

    assert result.confidence == 0.0
    assert result.total_weight == 0.0


def test_empty_evidence_is_rejected():
    engine = WeightedEvidenceEngine()

    with pytest.raises(ValueError):
        engine.evaluate([])


def test_similarity_must_be_bounded():
    with pytest.raises(ValueError):
        Evidence(
            similarity=1.1,
            success=True,
        )