from heos.coordination import CoordinationContext, CoordinationState


def test_default_context():
    ctx = CoordinationContext(cycle_id="cycle-1")

    assert ctx.cycle_id == "cycle-1"
    assert ctx.state == "CREATED"
    assert ctx.request == {}
    assert ctx.metadata == {}


def test_state_enum():
    assert CoordinationState.CREATED.value == "CREATED"
    assert CoordinationState.EXECUTING.value == "EXECUTING"
