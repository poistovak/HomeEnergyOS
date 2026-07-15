from __future__ import annotations

import json
from datetime import UTC, datetime
from .canonical import sha256_hex
from .claims import evaluate_claims
from .integrity import certificate_fingerprint, certificate_id_for
from .models import (
    CertifiedDecision,
    DecisionCertificate,
    VerificationCode,
    VerificationIssue,
    VerificationReport,
)
from .policy import parse_policy_json


def _issue(code: VerificationCode, detail: str) -> VerificationIssue:
    return VerificationIssue(code=code, critical=True, detail=detail)


class ProofVerifier:
    def verify(
        self,
        certified: CertifiedDecision,
        *,
        verified_at: datetime | None = None,
        previous_certificate: DecisionCertificate | CertifiedDecision | None = None,
    ) -> VerificationReport:
        certificate = certified.certificate
        now = verified_at or datetime.now(UTC)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("verified_at must be timezone-aware")
        issues: list[VerificationIssue] = []
        recomputed_id = certificate_id_for(certificate)
        if recomputed_id != certificate.certificate_id:
            issues.append(_issue(VerificationCode.CERTIFICATE_ID, "certificate id does not match its canonical contents"))
        try:
            snapshot = json.loads(certified.release_snapshot_json)
        except json.JSONDecodeError:
            snapshot = {}
            issues.append(_issue(VerificationCode.RELEASE_SNAPSHOT, "release snapshot is not valid JSON"))
        try:
            policy = parse_policy_json(certified.proof_policy_json)
        except (ValueError, json.JSONDecodeError, TypeError):
            policy = {}
            issues.append(_issue(VerificationCode.POLICY, "proof policy is not valid JSON"))
        if sha256_hex(certified.release_snapshot_json) != certificate.release_snapshot_digest:
            issues.append(_issue(VerificationCode.RELEASE_SNAPSHOT, "release snapshot digest mismatch"))
        if sha256_hex(certified.state_snapshot_json) != certificate.state_digest:
            issues.append(_issue(VerificationCode.STATE_SNAPSHOT, "state snapshot digest mismatch"))
        if sha256_hex(certified.manifest_versions) != certificate.manifest_digest:
            issues.append(_issue(VerificationCode.MANIFEST, "manifest digest mismatch"))
        if sha256_hex(certified.model_versions) != certificate.model_digest:
            issues.append(_issue(VerificationCode.MODEL_VERSIONS, "model version digest mismatch"))
        policy_payload = {
            "proof_policy": policy,
            "release_policy_version": snapshot.get("policy_version"),
        }
        if sha256_hex(policy_payload) != certificate.policy_digest:
            issues.append(_issue(VerificationCode.POLICY, "policy digest mismatch"))
        if sha256_hex(certified.alternative_snapshots_json) != certificate.alternatives_digest:
            issues.append(_issue(VerificationCode.ALTERNATIVES, "alternative digest mismatch"))
        intent = snapshot.get("intent") if isinstance(snapshot, dict) else None
        action_payload = {
            "compiler_target": certified.compiler_target,
            "requested_mode": certified.requested_mode,
            "control_payload": certified.control_payload,
            "intent_id": intent.get("intent_id") if isinstance(intent, dict) else None,
            "source_decision_id": intent.get("source_decision_id") if isinstance(intent, dict) else None,
        }
        if sha256_hex(action_payload) != certificate.action_digest:
            issues.append(_issue(VerificationCode.ACTION, "action digest mismatch"))
        if snapshot.get("release_id") != certificate.release_id:
            issues.append(_issue(VerificationCode.RELEASE_SNAPSHOT, "release id is not bound to the certificate"))
        if snapshot.get("source_decision_id") != certificate.source_decision_id:
            issues.append(_issue(VerificationCode.SOURCE_BINDING, "source decision id is not bound to the certificate"))
        if snapshot.get("status") != "released":
            issues.append(_issue(VerificationCode.RELEASE_STATUS, "release snapshot is not released"))
        if not isinstance(intent, dict):
            issues.append(_issue(VerificationCode.INTENT, "release snapshot does not contain an intent"))
        else:
            if intent.get("intent_id") != certificate.intent_id:
                issues.append(_issue(VerificationCode.INTENT, "intent id is not bound to the certificate"))
            if intent.get("source_decision_id") != certificate.source_decision_id:
                issues.append(_issue(VerificationCode.SOURCE_BINDING, "intent source id differs from release source id"))
            if intent.get("compiler_target") != certified.compiler_target:
                issues.append(_issue(VerificationCode.COMPILER_TARGET, "compiler target differs from the release snapshot"))
            snapshot_payload = tuple((str(key), float(value)) for key, value in intent.get("control_payload", ()))
            if snapshot_payload != certified.control_payload:
                issues.append(_issue(VerificationCode.ACTION, "control payload differs from the release snapshot"))
        if any(not bool(item.get("passed")) for item in snapshot.get("gates", ())):
            issues.append(_issue(VerificationCode.GATES, "release snapshot contains a failed gate"))
        if now < certificate.issued_at or now > certificate.expires_at:
            issues.append(_issue(VerificationCode.VALIDITY_WINDOW, "certificate is outside its execution validity window"))
        previous = None
        if previous_certificate is not None:
            previous = (
                previous_certificate.certificate
                if isinstance(previous_certificate, CertifiedDecision)
                else previous_certificate
            )
        expected_previous = certificate_fingerprint(previous) if previous is not None else None
        if certificate.previous_certificate_hash != expected_previous:
            issues.append(_issue(VerificationCode.CHAIN_LINK, "previous certificate hash does not match"))
        try:
            expected_claims = evaluate_claims(
                snapshot=snapshot,
                state_snapshot_json=certified.state_snapshot_json,
                compiler_target=certified.compiler_target,
                control_payload=certified.control_payload,
                manifest_versions=certified.manifest_versions,
                model_versions=certified.model_versions,
                alternative_snapshots_json=certified.alternative_snapshots_json,
                issued_at=certificate.issued_at,
                allowed_compiler_targets=tuple(policy["allowed_compiler_targets"]),
                required_model_components=tuple(policy["required_model_components"]),
                maximum_clock_skew_seconds=float(policy["maximum_clock_skew_seconds"]),
                require_all_release_gates_passed=bool(policy["require_all_release_gates_passed"]),
                require_chain_link=bool(policy["require_chain_link"]),
                previous_certificate_hash=certificate.previous_certificate_hash,
            )
        except (KeyError, TypeError, ValueError):
            expected_claims = ()
            issues.append(_issue(VerificationCode.CLAIMS, "claims cannot be recomputed from the proof policy"))
        if expected_claims != certificate.claims:
            issues.append(_issue(VerificationCode.CLAIMS, "stored claims differ from recomputed evidence"))
        if any(not item.passed for item in certificate.claims):
            issues.append(_issue(VerificationCode.CLAIMS, "certificate contains a failed claim"))
        return VerificationReport(
            certificate_id=certificate.certificate_id,
            verified_at=now,
            valid=not issues,
            issues=tuple(issues),
            recomputed_certificate_id=recomputed_id,
            checked_claims=len(expected_claims),
        )
