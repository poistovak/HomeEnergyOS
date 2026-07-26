import pytest

from heos.policy.mode_policy import ModePolicy
from heos.release_gate import OperationMode, mode_rank


@pytest.mark.parametrize(
    ("maximum", "requested", "expected"),
    [
        (
            OperationMode.OBSERVE,
            OperationMode.OBSERVE,
            OperationMode.OBSERVE,
        ),
        (
            OperationMode.ADVISE,
            OperationMode.OBSERVE,
            OperationMode.OBSERVE,
        ),
        (
            OperationMode.ADVISE,
            OperationMode.ADVISE,
            OperationMode.ADVISE,
        ),
        (
            OperationMode.SUPERVISED,
            OperationMode.SUPERVISED,
            OperationMode.SUPERVISED,
        ),
        (
            OperationMode.AUTONOMOUS,
            OperationMode.AUTONOMOUS,
            OperationMode.AUTONOMOUS,
        ),
        (
            OperationMode.ADVISE,
            OperationMode.AUTONOMOUS,
            OperationMode.ADVISE,
        ),
        (
            OperationMode.SUPERVISED,
            OperationMode.AUTONOMOUS,
            OperationMode.SUPERVISED,
        ),
    ],
)
def test_mode_policy_resolves_effective_mode(
    maximum,
    requested,
    expected,
):
    result = ModePolicy(
        maximum_mode=maximum,
    ).resolve(requested)

    assert result.effective_mode is expected
    assert result.downgraded is (
        expected is not requested
    )


def test_mode_policy_explains_downgrade():
    result = ModePolicy(
        maximum_mode=OperationMode.ADVISE,
    ).resolve(
        OperationMode.AUTONOMOUS,
    )

    assert result.downgraded is True
    assert "autonomous" in result.reason
    assert "advise" in result.reason
@pytest.mark.parametrize(
    ("maximum", "requested"),
    [
        (OperationMode.OBSERVE, OperationMode.OBSERVE),
        (OperationMode.ADVISE, OperationMode.OBSERVE),
        (OperationMode.ADVISE, OperationMode.ADVISE),
        (OperationMode.SUPERVISED, OperationMode.OBSERVE),
        (OperationMode.SUPERVISED, OperationMode.ADVISE),
        (OperationMode.SUPERVISED, OperationMode.SUPERVISED),
        (OperationMode.AUTONOMOUS, OperationMode.OBSERVE),
        (OperationMode.AUTONOMOUS, OperationMode.ADVISE),
        (OperationMode.AUTONOMOUS, OperationMode.SUPERVISED),
        (OperationMode.AUTONOMOUS, OperationMode.AUTONOMOUS),
    ],
)
def test_mode_policy_never_escalates_requested_mode(
    maximum,
    requested,
):
    result = ModePolicy(
        maximum_mode=maximum,
    ).resolve(requested)

    assert mode_rank(result.effective_mode) <= mode_rank(requested)


@pytest.mark.parametrize(
    ("maximum", "requested"),
    [
        (OperationMode.OBSERVE, OperationMode.ADVISE),
        (OperationMode.OBSERVE, OperationMode.SUPERVISED),
        (OperationMode.OBSERVE, OperationMode.AUTONOMOUS),
        (OperationMode.ADVISE, OperationMode.SUPERVISED),
        (OperationMode.ADVISE, OperationMode.AUTONOMOUS),
        (OperationMode.SUPERVISED, OperationMode.AUTONOMOUS),
    ],
)
def test_mode_policy_downgrade_never_exceeds_maximum(
    maximum,
    requested,
):
    result = ModePolicy(
        maximum_mode=maximum,
    ).resolve(requested)

    assert mode_rank(result.effective_mode) <= mode_rank(maximum)
    assert result.downgraded is True