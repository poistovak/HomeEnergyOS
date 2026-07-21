from heos.coordination.context import CoordinationContext
from heos.coordination.coordinator import CoordinationCoordinator
from heos.coordination.state import CoordinationState


def test_heos_contract_start():
    ctx = CoordinationContext(cycle_id="final")

    result = CoordinationCoordinator().start(ctx)

    assert result is ctx
    assert ctx.state == CoordinationState.PLANNING.value


def test_context_has_cycle_id():
    assert CoordinationContext(cycle_id="x").cycle_id == "x"


def test_context_default_source():
    assert CoordinationContext(cycle_id="x").source == "unknown"


def test_context_default_state():
    assert CoordinationContext(cycle_id="x").state == "CREATED"


def test_context_request_default():
    assert CoordinationContext(cycle_id="x").request == {}


def test_context_metadata_default():
    assert CoordinationContext(cycle_id="x").metadata == {}


def test_state_enum_size():
    assert len(CoordinationState) == 10


def test_state_contains_completed():
    assert CoordinationState.COMPLETED.value == "COMPLETED"


def test_state_contains_failed():
    assert CoordinationState.FAILED.value == "FAILED"