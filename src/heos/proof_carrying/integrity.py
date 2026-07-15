from __future__ import annotations

from typing import Any

from .canonical import sha256_hex
from .models import DecisionCertificate, EvidenceClaim


def claim_to_dict(claim: EvidenceClaim) -> dict[str, Any]:
    return {
        "code": claim.code.value,
        "passed": claim.passed,
        "critical": claim.critical,
        "detail": claim.detail,
        "evidence_hash": claim.evidence_hash,
    }


def unsigned_certificate_dict(certificate: DecisionCertificate) -> dict[str, Any]:
    return {
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
        "claims": [claim_to_dict(item) for item in certificate.claims],
        "proof_policy_version": certificate.proof_policy_version,
        "schema_version": certificate.schema_version,
        "hash_algorithm": certificate.hash_algorithm.value,
        "metadata": [list(item) for item in certificate.metadata],
    }


def certificate_id_for(certificate: DecisionCertificate) -> str:
    return "pcd-" + sha256_hex(unsigned_certificate_dict(certificate))


def certificate_fingerprint(certificate: DecisionCertificate) -> str:
    payload = {
        "certificate_id": certificate.certificate_id,
        **unsigned_certificate_dict(certificate),
    }
    return sha256_hex(payload)
