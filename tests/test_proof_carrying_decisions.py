from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import inf, nan
from types import SimpleNamespace

import pytest

from heos.proof_carrying import (
    CertifiedDecision,
    ChainAuditReport,
    ClaimCode,
    DecisionCertificate,
    EvidenceClaim,
    InMemoryProofRepository,
    ProofBuilder,
    ProofBuildError,
    ProofCarryingDecisionEngine,
    ProofPolicy,
    ProofVerifier,
    VerificationCode,
    audit_chain,
    canonical_json,
    certificate_fingerprint,
    certificate_id_for,
    dumps_certified_decision,
    loads_certified_decision,
    normalize_versions,
    replay_envelope,
    sha256_hex,
    to_primitive,
)

NOW = datetime(2026, 7, 15, 20, 0, tzinfo=UTC)


class Value(StrEnum):
    RELEASED = "released"
    HELD = "held"
    ADVISE = "advise"


@dataclass(frozen=True, slots=True)
class Gate:
    code: str
    passed: bool = True
    critical: bool = True
    detail: str = "passed"


@dataclass(frozen=True, slots=True)
class Intent:
    intent_id: str = "intent-1"
    source_decision_id: str = "strategy-1"
    candidate_id: str = "candidate-balanced"
    requested_mode: Value = Value.ADVISE
    created_at: datetime = NOW
    not_after: datetime = NOW + timedelta(minutes=15)
    compiler_target: str = "heos.decision_compiler"
    control_payload: tuple[tuple[str, float], ...] = (
        ("battery_power_kw", 1.0),
        ("ev_charge_kw", 3.6),
        ("hvac_thermal_kw", 2.0),
    )
    metadata: tuple[tuple[str, str], ...] = (("release_id", "release-1"),)


@dataclass(frozen=True, slots=True)
class Release:
    release_id: str = "release-1"
    source_decision_id: str = "strategy-1"
    evaluated_at: datetime = NOW
    requested_mode: Value = Value.ADVISE
    status: Value = Value.RELEASED
    gates: tuple[Gate, ...] = (
        Gate("manifest_complete"),
        Gate("safety_ready"),
        Gate("executor_ready"),
    )
    policy_version: str = "release-policy-1"
    manifest_schema_version: str = "heos-release-manifest-1"
    intent: Intent | None = Intent()
    explanation: str = "Operational release gate passed."
    metadata: tuple[tuple[str, str], ...] = (("site", "lab"),)


MANIFEST = {
    "forecast": "forecast-1",
    "feedback": "feedback-1",
    "memory": "memory-1",
    "digital_twin": "digital-twin-1",
    "calibration": "calibration-1",
    "strategy": "strategy-1",
    "compiler": "compiler-1",
    "safety": "safety-1",
    "execution": "execution-1",
    "release_gate": "release-gate-1",
}
STATE = {
    "timestamp": NOW,
    "grid_kw": 0.4,
    "pv_kw": 6.2,
    "battery_soc": 0.64,
    "ev_soc": 0.42,
    "indoor_c": 21.5,
}
ALTERNATIVES = (
    {"candidate_id": "candidate-cost", "objective_score": 1.31},
    {"candidate_id": "candidate-comfort", "objective_score": 1.55},
)


def build(
    release: Release | None = None,
    *,
    policy: ProofPolicy | None = None,
    previous: CertifiedDecision | DecisionCertificate | None = None,
    issued_at: datetime = NOW,
    state: object = STATE,
    manifest: object = MANIFEST,
    models: object | None = None,
    alternatives: object = ALTERNATIVES,
) -> CertifiedDecision:
    return ProofBuilder(policy).certify(
        release or Release(),
        state_snapshot=state,
        manifest_versions=manifest,
        model_versions=models,
        rejected_alternatives=alternatives,
        previous_certificate=previous,
        issued_at=issued_at,
        metadata=(("site", "home"),),
    )


def verify(
    decision: CertifiedDecision,
    *,
    at: datetime = NOW,
    previous: CertifiedDecision | DecisionCertificate | None = None,
):
    return ProofVerifier().verify(decision, verified_at=at, previous_certificate=previous)


def test_builds_valid_certificate() -> None:
    decision = build()
    report = verify(decision)
    assert report.valid
    assert decision.certificate.certificate_id.startswith("pcd-")
    assert decision.certificate.all_claims_passed


def test_certificate_has_every_required_claim() -> None:
    decision = build()
    assert {item.code for item in decision.certificate.claims} == set(ClaimCode)


def test_certificate_id_is_deterministic() -> None:
    assert build().certificate.certificate_id == build().certificate.certificate_id


def test_certificate_id_changes_with_state() -> None:
    changed = {**STATE, "battery_soc": 0.65}
    assert build().certificate.certificate_id != build(state=changed).certificate.certificate_id


def test_certificate_id_changes_with_action() -> None:
    intent = replace(Intent(), control_payload=(("ev_charge_kw", 2.0),))
    assert build().certificate.certificate_id != build(replace(Release(), intent=intent)).certificate.certificate_id


def test_certificate_id_changes_with_manifest() -> None:
    changed = {**MANIFEST, "strategy": "strategy-2"}
    assert build().certificate.certificate_id != build(manifest=changed).certificate.certificate_id


def test_certificate_id_changes_with_alternatives() -> None:
    changed = (*ALTERNATIVES, {"candidate_id": "reserve", "objective_score": 2.0})
    assert build().certificate.certificate_id != build(alternatives=changed).certificate.certificate_id


def test_certificate_fingerprint_is_stable() -> None:
    certificate = build().certificate
    assert certificate_fingerprint(certificate) == certificate_fingerprint(certificate)


def test_certificate_id_recomputes() -> None:
    certificate = build().certificate
    assert certificate_id_for(certificate) == certificate.certificate_id


def test_released_decision_is_required() -> None:
    with pytest.raises(ProofBuildError, match="released"):
        build(replace(Release(), status=Value.HELD))


def test_intent_is_required() -> None:
    with pytest.raises(ProofBuildError, match="execution intent"):
        build(replace(Release(), intent=None))


def test_all_release_gates_must_pass() -> None:
    gates = (Gate("safety_ready", False, True, "not ready"),)
    with pytest.raises(ProofBuildError, match="all_gates_passed"):
        build(replace(Release(), gates=gates))


def test_policy_can_record_nonpassing_gate_without_requiring_it() -> None:
    gates = (Gate("noncritical", False, False, "optional"),)
    policy = ProofPolicy(require_all_release_gates_passed=False)
    decision = build(replace(Release(), gates=gates), policy=policy)
    assert decision.certificate.all_claims_passed


def test_compiler_target_must_be_allowed() -> None:
    intent = replace(Intent(), compiler_target="heos.device")
    with pytest.raises(ProofBuildError, match="compiler_target_allowed"):
        build(replace(Release(), intent=intent))


def test_custom_compiler_target_can_be_allowed() -> None:
    intent = replace(Intent(), compiler_target="heos.compiler.v2")
    policy = ProofPolicy(allowed_compiler_targets=("heos.compiler.v2",))
    assert build(replace(Release(), intent=intent), policy=policy).compiler_target == "heos.compiler.v2"


@pytest.mark.parametrize("issued_at", [NOW - timedelta(seconds=31), NOW + timedelta(minutes=15, seconds=1)])
def test_certificate_must_be_issued_in_intent_window(issued_at: datetime) -> None:
    with pytest.raises(ProofBuildError, match="intent_window_valid"):
        build(issued_at=issued_at)


@pytest.mark.parametrize("issued_at", [NOW - timedelta(seconds=30), NOW, NOW + timedelta(minutes=14, seconds=59)])
def test_intent_window_boundaries_are_accepted(issued_at: datetime) -> None:
    assert build(issued_at=issued_at).certificate.issued_at == issued_at


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_nonfinite_control_values_are_rejected(value: float) -> None:
    intent = replace(Intent(), control_payload=(("ev_charge_kw", value),))
    with pytest.raises((ProofBuildError, ValueError)):
        build(replace(Release(), intent=intent))


def test_duplicate_control_keys_are_rejected() -> None:
    intent = replace(Intent(), control_payload=(("power", 1.0), ("power", 2.0)))
    with pytest.raises((ProofBuildError, ValueError)):
        build(replace(Release(), intent=intent))


def test_manifest_is_required() -> None:
    with pytest.raises(ProofBuildError, match="manifest_versions"):
        build(manifest=())



def test_null_state_is_rejected() -> None:
    with pytest.raises(ProofBuildError, match="state_snapshot"):
        build(state=None)

def test_required_models_are_derived_from_manifest() -> None:
    decision = build()
    assert {name for name, _ in decision.model_versions} == {"digital_twin", "calibration", "strategy"}


def test_missing_required_model_is_rejected() -> None:
    manifest = {key: value for key, value in MANIFEST.items() if key != "calibration"}
    with pytest.raises(ProofBuildError, match="model_versions_bound"):
        build(manifest=manifest)


def test_explicit_model_versions_must_be_in_manifest() -> None:
    models = {"digital_twin": "x", "calibration": "x", "strategy": "x", "alien": "1"}
    with pytest.raises(ProofBuildError, match="model_versions_bound"):
        build(models=models)


def test_chain_root_is_valid_by_default() -> None:
    decision = build()
    assert decision.certificate.previous_certificate_hash is None
    assert verify(decision).valid


def test_chain_link_binds_previous_certificate() -> None:
    first = build()
    second_release = replace(
        Release(),
        release_id="release-2",
        source_decision_id="strategy-2",
        intent=replace(Intent(), intent_id="intent-2", source_decision_id="strategy-2"),
    )
    second = build(second_release, previous=first)
    assert second.certificate.previous_certificate_hash == certificate_fingerprint(first.certificate)
    assert verify(second, previous=first).valid


def test_chain_link_requires_previous_during_verification() -> None:
    first = build()
    second_release = replace(
        Release(),
        release_id="release-2",
        source_decision_id="strategy-2",
        intent=replace(Intent(), intent_id="intent-2", source_decision_id="strategy-2"),
    )
    second = build(second_release, previous=first)
    report = verify(second)
    assert not report.valid
    assert VerificationCode.CHAIN_LINK in {item.code for item in report.issues}


def test_policy_can_require_chain_link() -> None:
    with pytest.raises(ProofBuildError, match="chain_bound"):
        build(policy=ProofPolicy(require_chain_link=True))


def test_policy_required_chain_accepts_predecessor() -> None:
    first = build()
    second_release = replace(
        Release(),
        release_id="release-2",
        source_decision_id="strategy-2",
        intent=replace(Intent(), intent_id="intent-2", source_decision_id="strategy-2"),
    )
    decision = build(second_release, policy=ProofPolicy(require_chain_link=True), previous=first)
    assert verify(decision, previous=first).valid


def test_tampered_state_is_detected() -> None:
    decision = build()
    tampered = replace(decision, state_snapshot_json=canonical_json({"battery_soc": 0.01}))
    report = verify(tampered)
    assert not report.valid
    assert VerificationCode.STATE_SNAPSHOT in {item.code for item in report.issues}


def test_tampered_action_is_detected() -> None:
    decision = build()
    tampered = replace(decision, control_payload=(("ev_charge_kw", 9.9),))
    report = verify(tampered)
    assert not report.valid
    assert VerificationCode.ACTION in {item.code for item in report.issues}


def test_tampered_manifest_is_detected() -> None:
    decision = build()
    tampered = replace(decision, manifest_versions=((*decision.manifest_versions[:-1], ("strategy", "evil"))))
    assert not verify(tampered).valid


def test_tampered_models_are_detected() -> None:
    decision = build()
    tampered = replace(decision, model_versions=(("calibration", "evil"), ("digital_twin", "x"), ("strategy", "x")))
    assert not verify(tampered).valid


def test_tampered_policy_is_detected() -> None:
    decision = build()
    payload = json.loads(decision.proof_policy_json)
    payload["allowed_compiler_targets"] = ["heos.device"]
    tampered = replace(decision, proof_policy_json=canonical_json(payload))
    assert not verify(tampered).valid


def test_tampered_alternative_is_detected() -> None:
    decision = build()
    tampered = replace(decision, alternative_snapshots_json=(canonical_json({"candidate_id": "evil"}),))
    assert not verify(tampered).valid


def test_tampered_release_snapshot_is_detected() -> None:
    decision = build()
    payload = json.loads(decision.release_snapshot_json)
    payload["status"] = "held"
    tampered = replace(decision, release_snapshot_json=canonical_json(payload))
    report = verify(tampered)
    assert not report.valid
    assert VerificationCode.RELEASE_STATUS in {item.code for item in report.issues}


def test_tampered_certificate_id_is_detected() -> None:
    decision = build()
    certificate = replace(decision.certificate, certificate_id="pcd-tampered")
    report = verify(replace(decision, certificate=certificate))
    assert VerificationCode.CERTIFICATE_ID in {item.code for item in report.issues}


def test_tampered_claim_is_detected() -> None:
    decision = build()
    claims = list(decision.certificate.claims)
    claims[0] = replace(claims[0], detail="tampered")
    certificate = replace(decision.certificate, claims=tuple(claims))
    report = verify(replace(decision, certificate=certificate))
    assert VerificationCode.CLAIMS in {item.code for item in report.issues}


def test_expired_certificate_is_rejected() -> None:
    decision = build()
    report = verify(decision, at=NOW + timedelta(minutes=16))
    assert not report.valid
    assert VerificationCode.VALIDITY_WINDOW in {item.code for item in report.issues}


def test_certificate_before_issue_is_rejected() -> None:
    decision = build()
    report = verify(decision, at=NOW - timedelta(seconds=1))
    assert not report.valid


def test_serialization_round_trip() -> None:
    decision = build()
    assert loads_certified_decision(dumps_certified_decision(decision)) == decision


def test_serialization_is_deterministic() -> None:
    decision = build()
    assert dumps_certified_decision(decision) == dumps_certified_decision(decision)


def test_serialization_rejects_nonobject() -> None:
    with pytest.raises(ValueError, match="object"):
        loads_certified_decision("[]")


def test_repository_append_is_idempotent() -> None:
    repository = InMemoryProofRepository()
    decision = build()
    assert repository.append(decision) is decision
    assert repository.append(decision) is decision
    assert len(repository) == 1


def test_repository_rejects_same_id_with_different_content() -> None:
    repository = InMemoryProofRepository()
    decision = build()
    repository.append(decision)
    altered = replace(decision, state_snapshot_json=canonical_json({"x": 1}))
    with pytest.raises(ValueError, match="different content"):
        repository.append(altered)


def test_repository_queries_by_release() -> None:
    decision = build()
    repository = InMemoryProofRepository((decision,))
    assert repository.by_release("release-1") == (decision,)
    assert repository.by_release("missing") == ()


def test_repository_last() -> None:
    first = build()
    repository = InMemoryProofRepository((first,))
    assert repository.last() == first


def test_empty_repository_last_is_none() -> None:
    assert InMemoryProofRepository().last() is None


def test_engine_certifies_and_persists() -> None:
    engine = ProofCarryingDecisionEngine()
    decision = engine.certify(Release(), state_snapshot=STATE, manifest_versions=MANIFEST, issued_at=NOW)
    assert engine.repository.get(decision.certificate.certificate_id) == decision


def test_engine_links_to_repository_head() -> None:
    engine = ProofCarryingDecisionEngine()
    first = engine.certify(Release(), state_snapshot=STATE, manifest_versions=MANIFEST, issued_at=NOW)
    second_release = replace(
        Release(),
        release_id="release-2",
        source_decision_id="strategy-2",
        evaluated_at=NOW + timedelta(seconds=1),
        intent=replace(
            Intent(),
            intent_id="intent-2",
            source_decision_id="strategy-2",
            created_at=NOW + timedelta(seconds=1),
            not_after=NOW + timedelta(minutes=15),
        ),
    )
    second = engine.certify(
        second_release,
        state_snapshot=STATE,
        manifest_versions=MANIFEST,
        issued_at=NOW + timedelta(seconds=1),
        link_to_repository_head=True,
    )
    assert second.certificate.previous_certificate_hash == certificate_fingerprint(first.certificate)


def test_engine_verify_delegates() -> None:
    engine = ProofCarryingDecisionEngine()
    decision = engine.certify(Release(), state_snapshot=STATE, manifest_versions=MANIFEST, issued_at=NOW)
    assert engine.verify(decision, verified_at=NOW).valid


def test_audit_chain_accepts_valid_chain() -> None:
    first = build()
    second_release = replace(
        Release(),
        release_id="release-2",
        source_decision_id="strategy-2",
        intent=replace(Intent(), intent_id="intent-2", source_decision_id="strategy-2"),
    )
    second = build(second_release, previous=first)
    report = audit_chain((first, second))
    assert report.valid
    assert report.length == 2
    assert report.head_hash == certificate_fingerprint(second.certificate)


def test_audit_chain_detects_broken_link() -> None:
    first = build()
    second = build(replace(Release(), release_id="release-2"))
    report = audit_chain((first, second))
    assert not report.valid
    assert report.issues[0].index == 1


def test_audit_empty_chain() -> None:
    assert audit_chain(()) == ChainAuditReport(valid=True, length=0, head_hash=None)


def test_replay_envelope_is_deterministic() -> None:
    decision = build()
    assert replay_envelope(decision) == replay_envelope(decision)


def test_replay_envelope_contains_bound_inputs() -> None:
    decision = build()
    envelope = replay_envelope(decision)
    assert envelope.replay_token.startswith("replay-")
    assert envelope.state_snapshot_json == decision.state_snapshot_json
    assert envelope.alternative_snapshots_json == decision.alternative_snapshots_json


def test_replay_token_changes_with_certificate() -> None:
    assert replay_envelope(build()).replay_token != replay_envelope(build(state={**STATE, "pv_kw": 7.0})).replay_token


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        7,
        1.5,
        "text",
        NOW,
        timedelta(seconds=3),
        Value.RELEASED,
        (1, 2),
        {"b": 2, "a": 1},
        {3, 1, 2},
    ],
)
def test_canonicalization_supports_expected_types(value: object) -> None:
    canonical_json(value)


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_canonicalization_rejects_nonfinite_floats(value: float) -> None:
    with pytest.raises(ValueError, match="non-finite"):
        canonical_json(value)


def test_canonical_json_sorts_mapping_keys() -> None:
    assert canonical_json({"z": 1, "a": 2}) == '{"a":2,"z":1}'


def test_sha256_hex_is_stable() -> None:
    assert sha256_hex({"a": 1}) == sha256_hex({"a": 1})
    assert len(sha256_hex({"a": 1})) == 64


def test_normalize_versions_sorts_items() -> None:
    assert normalize_versions({"z": "2", "a": "1"}) == (("a", "1"), ("z", "2"))


def test_normalize_versions_rejects_duplicates() -> None:
    with pytest.raises(ValueError, match="unique"):
        normalize_versions((("a", "1"), ("a", "2")))


def test_normalize_versions_rejects_empty_values() -> None:
    with pytest.raises(ValueError, match="empty"):
        normalize_versions((("a", ""),))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ProofPolicy(allowed_compiler_targets=()),
        lambda: ProofPolicy(required_model_components=()),
        lambda: ProofPolicy(maximum_clock_skew=timedelta(seconds=-1)),
        lambda: EvidenceClaim(ClaimCode.ACTION if hasattr(ClaimCode, "ACTION") else ClaimCode.STATE_BOUND, True, True, "x", "bad"),
        lambda: DecisionCertificate(
            certificate_id="x",
            release_id="r",
            source_decision_id="s",
            intent_id="i",
            issued_at=NOW,
            expires_at=NOW,
            action_digest="0" * 64,
            release_snapshot_digest="0" * 64,
            state_digest="0" * 64,
            manifest_digest="0" * 64,
            model_digest="0" * 64,
            policy_digest="0" * 64,
            alternatives_digest="0" * 64,
            previous_certificate_hash=None,
            claims=(EvidenceClaim(ClaimCode.STATE_BOUND, True, True, "x", "0" * 64),),
            proof_policy_version="p",
        ),
    ],
)
def test_model_validation_rejects_invalid_values(factory) -> None:
    with pytest.raises(ValueError):
        factory()


def test_claims_are_sorted() -> None:
    decision = build()
    values = [item.code.value for item in decision.certificate.claims]
    assert values == sorted(values)


def test_metadata_is_sorted() -> None:
    builder = ProofBuilder()
    decision = builder.certify(
        Release(),
        state_snapshot=STATE,
        manifest_versions=MANIFEST,
        issued_at=NOW,
        metadata=(("z", "2"), ("a", "1")),
    )
    assert decision.certificate.metadata == (("a", "1"), ("z", "2"))


def test_to_primitive_supports_regular_objects() -> None:
    value = SimpleNamespace(z=2, a=1)
    assert to_primitive(value) == {"a": 1, "z": 2}


def test_verification_report_counts_claims() -> None:
    decision = build()
    report = verify(decision)
    assert report.checked_claims == len(decision.certificate.claims)
