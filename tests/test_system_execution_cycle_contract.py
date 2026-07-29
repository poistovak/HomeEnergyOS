from __future__ import annotations

PIPELINE = (
    "forecast",
    "decision",
    "coordination",
    "recovery",
    "continuity",
    "execution",
    "outcome_verification",
    "feedback",
    "learning",
    "house_memory",
)


def test_pipeline_contains_every_major_layer():
    assert PIPELINE == (
        "forecast",
        "decision",
        "coordination",
        "recovery",
        "continuity",
        "execution",
        "outcome_verification",
        "feedback",
        "learning",
        "house_memory",
    )


def test_pipeline_has_no_duplicate_layers():
    assert len(PIPELINE) == len(set(PIPELINE))


def test_house_memory_is_last_stage():
    assert PIPELINE[-1] == "house_memory"


def test_forecast_is_first_stage():
    assert PIPELINE[0] == "forecast"


def test_execution_precedes_outcome_verification():
    assert PIPELINE.index("execution") < PIPELINE.index(
        "outcome_verification"
    )


def test_outcome_verification_precedes_feedback():
    assert PIPELINE.index("outcome_verification") < PIPELINE.index(
        "feedback"
    )


def test_feedback_precedes_learning():
    assert PIPELINE.index("feedback") < PIPELINE.index(
        "learning"
    )


def test_learning_precedes_house_memory():
    assert PIPELINE.index("learning") < PIPELINE.index(
        "house_memory"
    )