from datetime import UTC

from heos.coordination import (
    CoordinationContext,
    CoordinationState,
)


def test_context_defaults():
    ctx = CoordinationContext(cycle_id="cycle-1")

    assert ctx.cycle_id == "cycle-1"
    assert ctx.source == "unknown"
    assert ctx.state == "CREATED"
    assert ctx.request == {}
    assert ctx.metadata == {}
    assert ctx.created_at.tzinfo == UTC


def test_context_custom_values():
    ctx = CoordinationContext(
        cycle_id="abc",
        source="forecast",
        state="RUNNING",
        request={"power": 5000},
        metadata={"site": "home"},
    )

    assert ctx.source == "forecast"
    assert ctx.state == "RUNNING"
    assert ctx.request["power"] == 5000
    assert ctx.metadata["site"] == "home"


def test_context_default_dicts_are_independent():
    first = CoordinationContext(cycle_id="a")
    second = CoordinationContext(cycle_id="b")

    first.request["x"] = 1
    first.metadata["y"] = 2

    assert second.request == {}
    assert second.metadata == {}


def test_state_enum():
    assert CoordinationState.CREATED.value == "CREATED"
    assert CoordinationState.EXECUTING.value == "EXECUTING"


def test_default_context():
    ctx = CoordinationContext(cycle_id="cycle-1")

    assert ctx.cycle_id == "cycle-1"
    assert ctx.state == "CREATED"