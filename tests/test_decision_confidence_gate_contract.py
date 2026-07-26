import pytest

from heos.result_verification.decision_confidence_gate import (
    ConfidenceGateStatus,
    DecisionConfidenceGate,
)
from heos.result_verification.reasoning_orchestrator import (
    ReasoningResult,
)


def make_result(
    confidence: float,
) -> ReasoningResult:
    return ReasoningResult(
        decision="charge_battery",
        confidence=confidence,
    )


def test_gate_accepts_strong_reasoning():
    gate = DecisionConfidenceGate(
        minimum_confidence=0.6,
    )

    result = gate.evaluate(
        make_result(0.9)
    )

    assert result.status is ConfidenceGateStatus.ACCEPT
    assert result.accepted is True
    assert result.decision == "charge_battery"
    assert result.confidence == 0.9


def test_gate_abstains_on_weak_reasoning():
    gate = DecisionConfidenceGate(
        minimum_confidence=0.6,
    )

    result = gate.evaluate(
        make_result(0.4)
    )

    assert result.status is ConfidenceGateStatus.ABSTAIN
    assert result.accepted is False
    assert result.reason == (
        "insufficient evidence for autonomous decision"
    )


def test_gate_accepts_exact_threshold():
    gate = DecisionConfidenceGate(
        minimum_confidence=0.6,
    )

    result = gate.evaluate(
        make_result(0.6)
    )

    assert result.status is ConfidenceGateStatus.ACCEPT


def test_gate_can_be_configured_more_conservatively():
    gate = DecisionConfidenceGate(
        minimum_confidence=0.8,
    )

    result = gate.evaluate(
        make_result(0.7)
    )

    assert result.status is ConfidenceGateStatus.ABSTAIN


def test_gate_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        DecisionConfidenceGate(
            minimum_confidence=1.1,
        )


def test_gate_rejects_negative_threshold():
    with pytest.raises(ValueError):
        DecisionConfidenceGate(
            minimum_confidence=-0.1,
        )