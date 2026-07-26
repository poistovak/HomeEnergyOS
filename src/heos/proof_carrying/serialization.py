from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .models import (
    CertifiedDecision,
    ClaimCode,
    DecisionCertificate,
    EvidenceClaim,
    HashAlgorithm,
)


def certificate_to_dict(certificate: DecisionCertificate) -> dict[str, Any]:
    return {
        "certificate_id": certificate.certificate_id,
        "release_id": certificate.release_id,
        "source_decision_id": certificate.source_decision_id,
        "intent_id": certificate.intent_id,
        "issued_at": certificate.issued_at.isoformat(),
        "expires_at": certificate.expires_at.isoformat(),
        "action_digest": certificate.action_digest,
        "release_snapshot_digest": certificate.release_snapshot_digest,
        "state_digest": certificate.state_digest,
        "manifest_digest": certificate.manifest_digest,
        "model_digest": certificate.model_digest,
        "policy_digest": certificate.policy_digest,
        "alternatives_digest": certificate.alternatives_digest,
        "previous_certificate_hash": certificate.previous_certificate_hash,
        "claims": [
            {
                "code": item.code.value,
                "passed": item.passed,
                "critical": item.critical,
                "detail": item.detail,
                "evidence_hash": item.evidence_hash,
            }
            for item in certificate.claims
        ],
        "proof_policy_version": certificate.proof_policy_version,
        "schema_version": certificate.schema_version,
        "hash_algorithm": certificate.hash_algorithm.value,
        "metadata": [list(item) for item in certificate.metadata],
    }


def certificate_from_dict(payload: dict[str, Any]) -> DecisionCertificate:
    return DecisionCertificate(
        certificate_id=payload["certificate_id"],
        release_id=payload["release_id"],
        source_decision_id=payload["source_decision_id"],
        intent_id=payload["intent_id"],
        issued_at=datetime.fromisoformat(payload["issued_at"]),
        expires_at=datetime.fromisoformat(payload["expires_at"]),
        action_digest=payload["action_digest"],
        release_snapshot_digest=payload["release_snapshot_digest"],
        state_digest=payload["state_digest"],
        manifest_digest=payload["manifest_digest"],
        model_digest=payload["model_digest"],
        policy_digest=payload["policy_digest"],
        alternatives_digest=payload["alternatives_digest"],
        previous_certificate_hash=payload.get("previous_certificate_hash"),
        claims=tuple(
            EvidenceClaim(
                code=ClaimCode(item["code"]),
                passed=bool(item["passed"]),
                critical=bool(item["critical"]),
                detail=item["detail"],
                evidence_hash=item["evidence_hash"],
            )
            for item in payload["claims"]
        ),
        proof_policy_version=payload["proof_policy_version"],
        schema_version=payload["schema_version"],
        hash_algorithm=HashAlgorithm(payload["hash_algorithm"]),
        metadata=tuple((str(key), str(value)) for key, value in payload.get("metadata", ())),
    )


def certified_decision_to_dict(decision: CertifiedDecision) -> dict[str, Any]:
    return {
        "certificate": certificate_to_dict(decision.certificate),
        "release_snapshot_json": decision.release_snapshot_json,
        "state_snapshot_json": decision.state_snapshot_json,
        "proof_policy_json": decision.proof_policy_json,
        "compiler_target": decision.compiler_target,
        "requested_mode": decision.requested_mode,
        "control_payload": [list(item) for item in decision.control_payload],
        "manifest_versions": [list(item) for item in decision.manifest_versions],
        "model_versions": [list(item) for item in decision.model_versions],
        "alternative_snapshots_json": list(decision.alternative_snapshots_json),
    }


def certified_decision_from_dict(payload: dict[str, Any]) -> CertifiedDecision:
    return CertifiedDecision(
        certificate=certificate_from_dict(payload["certificate"]),
        release_snapshot_json=payload["release_snapshot_json"],
        state_snapshot_json=payload["state_snapshot_json"],
        proof_policy_json=payload["proof_policy_json"],
        compiler_target=payload["compiler_target"],
        requested_mode=payload["requested_mode"],
        control_payload=tuple((str(key), float(value)) for key, value in payload["control_payload"]),
        manifest_versions=tuple((str(key), str(value)) for key, value in payload["manifest_versions"]),
        model_versions=tuple((str(key), str(value)) for key, value in payload["model_versions"]),
        alternative_snapshots_json=tuple(str(item) for item in payload.get("alternative_snapshots_json", ())),
    )


def dumps_certified_decision(decision: CertifiedDecision) -> str:
    return json.dumps(certified_decision_to_dict(decision), sort_keys=True, separators=(",", ":"))


def loads_certified_decision(value: str) -> CertifiedDecision:
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise TypeError("certified decision JSON must contain an object")
    return certified_decision_from_dict(payload)

