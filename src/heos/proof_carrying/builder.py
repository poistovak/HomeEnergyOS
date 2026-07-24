from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime
from typing import Any

from .canonical import canonical_json, normalize_versions, sha256_hex
from .claims import evaluate_claims
from .integrity import certificate_fingerprint, certificate_id_for
from .models import CertifiedDecision, DecisionCertificate, HashAlgorithm, ProofPolicy
from .policy import proof_policy_json
from .snapshot import release_snapshot, release_snapshot_json


class ProofBuildError(ValueError):
    pass


class ProofBuilder:
    def __init__(self, policy: ProofPolicy | None = None) -> None:
        self._policy = policy or ProofPolicy()

    @property
    def policy(self) -> ProofPolicy:
        return self._policy

    def certify(
        self,
        release_decision: Any,
        *,
        state_snapshot: Any,
        manifest_versions: Iterable[tuple[str, str]] | dict[str, str],
        model_versions: Iterable[tuple[str, str]] | dict[str, str] | None = None,
        rejected_alternatives: Iterable[Any] = (),
        previous_certificate: DecisionCertificate | CertifiedDecision | None = None,
        issued_at: datetime | None = None,
        metadata: Iterable[tuple[str, str]] = (),
    ) -> CertifiedDecision:
        snapshot = release_snapshot(release_decision)
        intent = snapshot.get("intent")
        if snapshot.get("status") != "released":
            raise ProofBuildError("only released decisions can be certified")
        if not isinstance(intent, dict):
            raise ProofBuildError("released decision must contain an execution intent")
        certificate_time = issued_at or datetime.fromisoformat(snapshot["evaluated_at"])
        if certificate_time.tzinfo is None or certificate_time.utcoffset() is None:
            raise ProofBuildError("issued_at must be timezone-aware")
        manifest = normalize_versions(manifest_versions)
        if not manifest:
            raise ProofBuildError("manifest_versions must not be empty")
        if model_versions is None:
            required = set(self._policy.required_model_components)
            models = tuple(item for item in manifest if item[0] in required)
        else:
            models = normalize_versions(model_versions)
        alternatives_json = tuple(canonical_json(item) for item in rejected_alternatives)
        if state_snapshot is None:
            raise ProofBuildError("state_snapshot must not be null")
        state_json = canonical_json(state_snapshot)
        snapshot_json = release_snapshot_json(release_decision)
        policy_json = proof_policy_json(self._policy)
        target = str(intent["compiler_target"])
        requested_mode = str(intent["requested_mode"])
        control_payload = tuple((str(key), float(value)) for key, value in intent["control_payload"])
        previous_hash = None
        if previous_certificate is not None:
            certificate = (
                previous_certificate.certificate
                if isinstance(previous_certificate, CertifiedDecision)
                else previous_certificate
            )
            previous_hash = certificate_fingerprint(certificate)
        claims = evaluate_claims(
            snapshot=snapshot,
            state_snapshot_json=state_json,
            compiler_target=target,
            control_payload=control_payload,
            manifest_versions=manifest,
            model_versions=models,
            alternative_snapshots_json=alternatives_json,
            issued_at=certificate_time,
            allowed_compiler_targets=self._policy.allowed_compiler_targets,
            required_model_components=self._policy.required_model_components,
            maximum_clock_skew_seconds=self._policy.maximum_clock_skew.total_seconds(),
            require_all_release_gates_passed=self._policy.require_all_release_gates_passed,
            require_chain_link=self._policy.require_chain_link,
            previous_certificate_hash=previous_hash,
        )
        failed = tuple(item for item in claims if item.critical and not item.passed)
        if failed:
            codes = ", ".join(item.code.value for item in failed)
            raise ProofBuildError(f"proof claims failed: {codes}")
        action_payload = {
            "compiler_target": target,
            "requested_mode": requested_mode,
            "control_payload": control_payload,
            "intent_id": intent["intent_id"],
            "source_decision_id": intent["source_decision_id"],
        }
        policy_payload = {
            "proof_policy": json.loads(policy_json),
            "release_policy_version": snapshot["policy_version"],
        }
        placeholder = "pcd-pending"
        certificate = DecisionCertificate(
            certificate_id=placeholder,
            release_id=str(snapshot["release_id"]),
            source_decision_id=str(snapshot["source_decision_id"]),
            intent_id=str(intent["intent_id"]),
            issued_at=certificate_time,
            expires_at=datetime.fromisoformat(str(intent["not_after"])),
            action_digest=sha256_hex(action_payload),
            release_snapshot_digest=sha256_hex(snapshot_json),
            state_digest=sha256_hex(state_json),
            manifest_digest=sha256_hex(manifest),
            model_digest=sha256_hex(models),
            policy_digest=sha256_hex(policy_payload),
            alternatives_digest=sha256_hex(alternatives_json),
            previous_certificate_hash=previous_hash,
            claims=claims,
            proof_policy_version=self._policy.version,
            hash_algorithm=HashAlgorithm.SHA256,
            metadata=tuple((str(key), str(value)) for key, value in metadata),
        )
        certificate = replace(certificate, certificate_id=certificate_id_for(certificate))
        return CertifiedDecision(
            certificate=certificate,
            release_snapshot_json=snapshot_json,
            state_snapshot_json=state_json,
            proof_policy_json=policy_json,
            compiler_target=target,
            requested_mode=requested_mode,
            control_payload=control_payload,
            manifest_versions=manifest,
            model_versions=models,
            alternative_snapshots_json=alternatives_json,
        )
