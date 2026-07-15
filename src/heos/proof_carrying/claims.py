from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .canonical import sha256_hex
from .models import ClaimCode, EvidenceClaim
from .snapshot import control_payload_is_finite


def _claim(code: ClaimCode, passed: bool, detail: str, evidence: Any) -> EvidenceClaim:
    return EvidenceClaim(
        code=code,
        passed=passed,
        critical=True,
        detail=detail,
        evidence_hash=sha256_hex(evidence),
    )


def evaluate_claims(
    *,
    snapshot: dict[str, Any],
    state_snapshot_json: str,
    compiler_target: str,
    control_payload: tuple[tuple[str, float], ...],
    manifest_versions: tuple[tuple[str, str], ...],
    model_versions: tuple[tuple[str, str], ...],
    alternative_snapshots_json: tuple[str, ...],
    issued_at: datetime,
    allowed_compiler_targets: tuple[str, ...],
    required_model_components: tuple[str, ...],
    maximum_clock_skew_seconds: float,
    require_all_release_gates_passed: bool,
    require_chain_link: bool,
    previous_certificate_hash: str | None,
) -> tuple[EvidenceClaim, ...]:
    intent = snapshot.get("intent")
    status = str(snapshot.get("status", ""))
    release_id = str(snapshot.get("release_id", ""))
    source_id = str(snapshot.get("source_decision_id", ""))
    gates = tuple(snapshot.get("gates", ()))
    all_gates_passed = bool(gates) and all(bool(item.get("passed")) for item in gates)
    intent_present = isinstance(intent, dict)
    intent_source = str(intent.get("source_decision_id", "")) if intent_present else ""
    intent_release_bound = intent_source == source_id and bool(release_id) and bool(source_id)
    target_allowed = compiler_target in allowed_compiler_targets
    window_valid = False
    if intent_present:
        created_at = datetime.fromisoformat(str(intent["created_at"]))
        not_after = datetime.fromisoformat(str(intent["not_after"]))
        skew = timedelta(seconds=float(maximum_clock_skew_seconds))
        window_valid = created_at - skew <= issued_at <= not_after
    manifest_names = {name for name, _ in manifest_versions}
    model_names = {name for name, _ in model_versions}
    models_bound = set(required_model_components).issubset(model_names) and model_names.issubset(manifest_names)
    claims = (
        _claim(
            ClaimCode.RELEASE_STATUS,
            status == "released",
            "release status is released" if status == "released" else f"release status is {status or 'missing'}",
            {"status": status},
        ),
        _claim(
            ClaimCode.INTENT_PRESENT,
            intent_present,
            "execution intent is present" if intent_present else "execution intent is missing",
            {"intent": intent},
        ),
        _claim(
            ClaimCode.SOURCE_BOUND,
            intent_release_bound,
            "release and intent share the source decision id" if intent_release_bound else "source decision ids do not match",
            {"release_source": source_id, "intent_source": intent_source},
        ),
        _claim(
            ClaimCode.ALL_GATES_PASSED,
            all_gates_passed or not require_all_release_gates_passed,
            "all release gates passed" if all_gates_passed else "one or more release gates failed",
            {"gates": gates, "required": require_all_release_gates_passed},
        ),
        _claim(
            ClaimCode.COMPILER_TARGET_ALLOWED,
            target_allowed,
            "intent targets an allowed deterministic compiler" if target_allowed else "compiler target is not allowed",
            {"target": compiler_target, "allowed": allowed_compiler_targets},
        ),
        _claim(
            ClaimCode.INTENT_WINDOW_VALID,
            window_valid,
            "certificate was issued inside the intent validity window" if window_valid else "certificate is outside the intent validity window",
            {"issued_at": issued_at, "intent": intent, "clock_skew": maximum_clock_skew_seconds},
        ),
        _claim(
            ClaimCode.PAYLOAD_FINITE,
            control_payload_is_finite(control_payload),
            "control payload is finite and uniquely keyed" if control_payload_is_finite(control_payload) else "control payload is invalid",
            {"control_payload": control_payload},
        ),
        _claim(
            ClaimCode.MANIFEST_BOUND,
            bool(manifest_versions),
            "component manifest is cryptographically bound" if manifest_versions else "component manifest is empty",
            {"manifest_versions": manifest_versions},
        ),
        _claim(
            ClaimCode.MODEL_VERSIONS_BOUND,
            models_bound,
            "required model versions are present in the manifest" if models_bound else "required model versions are missing or unbound",
            {
                "model_versions": model_versions,
                "required": required_model_components,
                "manifest": manifest_versions,
            },
        ),
        _claim(
            ClaimCode.STATE_BOUND,
            bool(state_snapshot_json),
            "input state snapshot is cryptographically bound" if state_snapshot_json else "state snapshot is missing",
            {"state_snapshot_json": state_snapshot_json},
        ),
        _claim(
            ClaimCode.POLICY_BOUND,
            True,
            "release and proof policies are cryptographically bound",
            {"release_policy_version": snapshot.get("policy_version")},
        ),
        _claim(
            ClaimCode.ALTERNATIVES_BOUND,
            True,
            f"{len(alternative_snapshots_json)} rejected alternatives are cryptographically bound",
            {"alternative_snapshots_json": alternative_snapshots_json},
        ),
        _claim(
            ClaimCode.CHAIN_BOUND,
            (previous_certificate_hash is not None) or not require_chain_link,
            "certificate is linked to its predecessor" if previous_certificate_hash else "certificate is an allowed chain root",
            {"previous_certificate_hash": previous_certificate_hash, "required": require_chain_link},
        ),
    )
    return tuple(sorted(claims, key=lambda item: item.code.value))
