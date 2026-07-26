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


def make_gate(
    minimum_confidence: float = 0.6,
) -> AutonomyAdmissionGate:
    return AutonomyAdmissionGate(
        confidence_gate=DecisionConfidenceGate(
            minimum_confidence=minimum_confidence,
        )
    )


def test_strong_reasoning_is_admitted():
    gate = make_gate()

    result = gate.evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.9,
        )
    )

    assert result.status is AutonomyAdmissionStatus.ADMITTED
    assert result.admitted is True
    assert result.decision == "charge_battery"
    assert result.confidence == 0.9


def test_weak_reasoning_abstains_before_release():
    gate = make_gate()

    result = gate.evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.4,
        )
    )

    assert result.status is AutonomyAdmissionStatus.ABSTAINED
    assert result.admitted is False
    assert result.reason == (
        "insufficient evidence for autonomous decision"
    )


def test_exact_threshold_is_admitted():
    gate = make_gate(
        minimum_confidence=0.7,
    )

    result = gate.evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.7,
        )
    )

    assert result.status is AutonomyAdmissionStatus.ADMITTED


def test_admission_preserves_reasoning_decision():
    gate = make_gate()

    result = gate.evaluate(
        ReasoningResult(
            decision="reduce_charging",
            confidence=0.8,
        )
    )

    assert result.decision == "reduce_charging"


def test_admission_does_not_promote_low_confidence():
    gate = make_gate(
        minimum_confidence=0.8,
    )

    result = gate.evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.79,
        )
    )

    assert result.admitted is False