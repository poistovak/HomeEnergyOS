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


class ReleaseBoundarySpy:
    def __init__(self) -> None:
        self.calls = 0

    def evaluate(self) -> None:
        self.calls += 1


def pass_to_release_if_admitted(
    result: ReasoningResult,
    *,
    admission_gate: AutonomyAdmissionGate,
    release_boundary: ReleaseBoundarySpy,
) -> AutonomyAdmissionStatus:
    admission = admission_gate.evaluate(result)

    if not admission.admitted:
        return admission.status

    release_boundary.evaluate()

    return admission.status


def test_abstain_never_reaches_release_boundary():
    release = ReleaseBoundarySpy()

    status = pass_to_release_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.4,
        ),
        admission_gate=AutonomyAdmissionGate(
            confidence_gate=DecisionConfidenceGate(
                minimum_confidence=0.6,
            )
        ),
        release_boundary=release,
    )

    assert status is AutonomyAdmissionStatus.ABSTAINED
    assert release.calls == 0


def test_admitted_reasoning_reaches_release_boundary_once():
    release = ReleaseBoundarySpy()

    status = pass_to_release_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.9,
        ),
        admission_gate=AutonomyAdmissionGate(
            confidence_gate=DecisionConfidenceGate(
                minimum_confidence=0.6,
            )
        ),
        release_boundary=release,
    )

    assert status is AutonomyAdmissionStatus.ADMITTED
    assert release.calls == 1


def test_threshold_is_a_hard_boundary():
    release = ReleaseBoundarySpy()

    pass_to_release_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.599,
        ),
        admission_gate=AutonomyAdmissionGate(
            confidence_gate=DecisionConfidenceGate(
                minimum_confidence=0.6,
            )
        ),
        release_boundary=release,
    )

    assert release.calls == 0


def test_exact_threshold_may_reach_release_boundary():
    release = ReleaseBoundarySpy()

    pass_to_release_if_admitted(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.6,
        ),
        admission_gate=AutonomyAdmissionGate(
            confidence_gate=DecisionConfidenceGate(
                minimum_confidence=0.6,
            )
        ),
        release_boundary=release,
    )

    assert release.calls == 1