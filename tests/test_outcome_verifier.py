from dataclasses import replace

import pytest

from heos.outcome_verifier import (
    ExecutionEvidence,
    ExpectedOutcome,
    OutcomeStatus,
    OutcomeVerifier,
    VerificationPolicy,
)


def expected(**changes):
    values = {"command_id": "cmd-001", "incident_id": "incident-001", "metric": "grid_power", "target_min": -50.0, "target_max": 50.0, "deadline": 500, "source_digest": "digest26"}
    values.update(changes)
    return ExpectedOutcome(**values)


def evidence(**changes):
    values = {"command_id": "cmd-001", "observed_at": 200, "values": {"grid_power": 10.0}, "attempts_used": 1, "executor": "home_assistant"}
    values.update(changes)
    return ExecutionEvidence(**values)


def test_target_range_is_verified():
    cert = OutcomeVerifier().verify_outcome(expected(), evidence())
    assert cert.result.status is OutcomeStatus.VERIFIED
    assert cert.result.deviation == 0.0
    assert cert.verify()


def test_near_miss_is_degraded():
    cert = OutcomeVerifier().verify_outcome(expected(), evidence(values={"grid_power": 54.0}))
    assert cert.result.status is OutcomeStatus.DEGRADED
    assert cert.result.retry_recommended


def test_large_miss_fails():
    cert = OutcomeVerifier().verify_outcome(expected(), evidence(values={"grid_power": 100.0}))
    assert cert.result.status is OutcomeStatus.FAILED


def test_missing_metric_is_inconclusive():
    cert = OutcomeVerifier().verify_outcome(expected(), evidence(values={}))
    assert cert.result.status is OutcomeStatus.INCONCLUSIVE
    assert cert.result.retry_recommended


def test_retry_limit_stops_recommendation():
    verifier = OutcomeVerifier(policy=VerificationPolicy(retry_limit=2))
    cert = verifier.verify_outcome(expected(), evidence(values={}, attempts_used=2))
    assert not cert.result.retry_recommended


def test_command_mismatch_fails():
    cert = OutcomeVerifier().verify_outcome(expected(), evidence(command_id="other"))
    assert cert.result.status is OutcomeStatus.FAILED


def test_late_evidence_fails():
    cert = OutcomeVerifier().verify_outcome(expected(), evidence(observed_at=501))
    assert cert.result.status is OutcomeStatus.FAILED


def test_deterministic_result():
    first = OutcomeVerifier().verify_outcome(expected(), evidence())
    second = OutcomeVerifier().verify_outcome(expected(), evidence())
    assert first.result.result_id == second.result.result_id
    assert first.digest == second.digest


def test_ledger_chain_and_tamper_detection():
    verifier = OutcomeVerifier()
    first = verifier.verify_outcome(expected(), evidence())
    second = verifier.verify_outcome(expected(command_id="cmd-002"), evidence(command_id="cmd-002"))
    assert second.previous_digest == first.digest
    assert verifier.ledger.verify_chain()
    assert not replace(first, digest="0" * 64).verify()


def test_validation():
    with pytest.raises(ValueError):
        expected(target_min=10, target_max=0)
    with pytest.raises(ValueError):
        evidence(command_id="")
    with pytest.raises(ValueError):
        VerificationPolicy(degraded_tolerance=-1)


def test_json_export():
    exported = OutcomeVerifier().verify_outcome(expected(), evidence()).to_json()
    assert '"policy_version":"27.0.0"' in exported
    assert '"status":"verified"' in exported
