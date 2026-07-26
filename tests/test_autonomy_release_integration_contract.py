from heos.result_verification.autonomy_admission import (
    AutonomyAdmissionGate,
    AutonomyAdmissionStatus,
)
from heos.result_verification.decision_confidence_gate import (
    DecisionConfidenceGate,
)
from heos.result_verification.reasoning_orchestrator import (
    ReasoningResult,
)


class OperationalReleaseGateSpy:
    def __init__(self) -> None:
        self.calls = 0
        self.last_request = None

    def review(self, request):
        self.calls += 1
        self.last_request = request
        return object()


def review_if_admitted(
    result: ReasoningResult,
    *,
    admission_gate: AutonomyAdmissionGate,
    release_gate: OperationalReleaseGateSpy,
    request: object,
):
    admission = admission_gate.evaluate(result)

    if not admission.admitted:
        return admission, None

    release_decision = release_gate.review(request)

    return admission, release_decision


def make_admission_gate(
    minimum_confidence: float = 0.6,
) -> AutonomyAdmissionGate:
    return AutonomyAdmissionGate(
        confidence_gate=DecisionConfidenceGate(
            minimum_confidence=minimum_confidence,
        )
    )


def test_low_confidence_never_calls_operational_release_gate():
    release_gate = OperationalReleaseGateSpy()
    request = object()

    admission, release_decision = review_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.4,
        ),
        admission_gate=make_admission_gate(),
        release_gate=release_gate,
        request=request,
    )

    assert admission.status is AutonomyAdmissionStatus.ABSTAINED
    assert release_gate.calls == 0
    assert release_gate.last_request is None
    assert release_decision is None


def test_admitted_reasoning_calls_operational_release_gate_once():
    release_gate = OperationalReleaseGateSpy()
    request = object()

    admission, release_decision = review_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.9,
        ),
        admission_gate=make_admission_gate(),
        release_gate=release_gate,
        request=request,
    )

    assert admission.status is AutonomyAdmissionStatus.ADMITTED
    assert release_gate.calls == 1
    assert release_gate.last_request is request
    assert release_decision is not None


def test_below_threshold_is_hard_stop():
    release_gate = OperationalReleaseGateSpy()

    admission, release_decision = review_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.599,
        ),
        admission_gate=make_admission_gate(
            minimum_confidence=0.6,
        ),
        release_gate=release_gate,
        request=object(),
    )

    assert admission.admitted is False
    assert release_gate.calls == 0
    assert release_decision is None


def test_exact_threshold_may_enter_release_evaluation():
    release_gate = OperationalReleaseGateSpy()

    admission, release_decision = review_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.6,
        ),
        admission_gate=make_admission_gate(
            minimum_confidence=0.6,
        ),
        release_gate=release_gate,
        request=object(),
    )

    assert admission.admitted is True
    assert release_gate.calls == 1
    assert release_decision is not None