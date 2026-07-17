from dataclasses import replace

import pytest

from heos.resilience import (
    FaultSignal,
    IncidentClass,
    IncidentLedger,
    RecoveryMode,
    RecoveryPolicy,
    RecoveryStatus,
    ResilienceEngine,
)
from heos.resilience.classifier import build_incident, classify_signal


def signal(code="sensor_stale", severity=30, observed_at=100, source="meter"):
    return FaultSignal(
        source=source,
        code=code,
        severity=severity,
        observed_at=observed_at,
        details={"phase": 1},
    )


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("sensor_stale", IncidentClass.DATA_STALE),
        ("device_timeout", IncidentClass.DEVICE_UNAVAILABLE),
        ("device_offline", IncidentClass.DEVICE_UNAVAILABLE),
        ("constraint_breach", IncidentClass.CONSTRAINT_VIOLATION),
        ("model_drift", IncidentClass.MODEL_DRIFT),
        ("execution_mismatch", IncidentClass.EXECUTION_MISMATCH),
        ("other", IncidentClass.UNKNOWN),
    ],
)
def test_classifier(code, expected):
    assert classify_signal(signal(code=code)) is expected


def test_signal_validation():
    with pytest.raises(ValueError):
        signal(severity=101)
    with pytest.raises(ValueError):
        FaultSignal("", "x", 1, 1, {})


def test_incident_is_deterministic_for_input_order():
    a = signal(code="sensor_stale", observed_at=20)
    b = signal(code="device_timeout", severity=40, observed_at=10, source="evse")
    assert build_incident([a, b]) == build_incident([b, a])


def test_empty_incident_rejected():
    with pytest.raises(ValueError):
        build_incident([])


def test_low_severity_uses_fallback():
    certificate = ResilienceEngine().assess([signal()], now=200)
    decision = certificate.decision
    assert decision.mode is RecoveryMode.FALLBACK
    assert decision.status is RecoveryStatus.READY
    assert decision.fallback_strategy == "last_known_safe_plan"
    assert certificate.verify()


def test_high_severity_holds():
    certificate = ResilienceEngine().assess(
        [signal(code="device_timeout", severity=75)], now=200
    )
    assert certificate.decision.mode is RecoveryMode.HOLD
    assert certificate.decision.status is RecoveryStatus.BLOCKED


def test_critical_severity_safe_stops():
    certificate = ResilienceEngine().assess(
        [signal(code="constraint_breach", severity=95)], now=200
    )
    assert certificate.decision.mode is RecoveryMode.SAFE_STOP
    assert certificate.decision.status is RecoveryStatus.BLOCKED


def test_unknown_incident_degrades():
    certificate = ResilienceEngine().assess(
        [signal(code="unexpected", severity=20)], now=200
    )
    assert certificate.decision.mode is RecoveryMode.DEGRADE
    assert certificate.decision.status is RecoveryStatus.READY


def test_policy_threshold_validation():
    with pytest.raises(ValueError):
        RecoveryPolicy(hold_threshold=80, safe_stop_threshold=70)
    with pytest.raises(ValueError):
        RecoveryPolicy(decision_ttl=0)


def test_certificate_is_deterministic():
    first = ResilienceEngine().assess([signal()], now=200)
    second = ResilienceEngine().assess([signal()], now=200)
    assert first.digest == second.digest
    assert first.to_json() == second.to_json()


def test_tampering_is_detected():
    certificate = ResilienceEngine().assess([signal()], now=200)
    tampered = replace(certificate, digest="0" * 64)
    assert not tampered.verify()


def test_ledger_chain():
    engine = ResilienceEngine()
    first = engine.assess([signal()], now=200)
    second = engine.assess(
        [signal(code="device_timeout", observed_at=201)], now=201
    )
    assert second.previous_digest == first.digest
    assert engine.ledger.verify_chain()
    assert len(engine.ledger.entries()) == 2


def test_ledger_rejects_wrong_previous_digest():
    first = ResilienceEngine().assess([signal()], now=200)
    other = ResilienceEngine().assess(
        [signal(code="device_timeout")], now=200
    )
    ledger = IncidentLedger()
    ledger.append(first)
    with pytest.raises(ValueError):
        ledger.append(other)


def test_validity_window():
    policy = RecoveryPolicy(decision_ttl=60)
    certificate = ResilienceEngine(policy=policy).assess([signal()], now=1000)
    assert certificate.decision.valid_until == 1060
