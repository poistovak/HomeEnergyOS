from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import sha256_hex
from .models import CertifiedDecision


@dataclass(frozen=True, slots=True)
class ReplayEnvelope:
    replay_token: str
    certificate_id: str
    compiler_target: str
    requested_mode: str
    control_payload: tuple[tuple[str, float], ...]
    state_snapshot_json: str
    manifest_versions: tuple[tuple[str, str], ...]
    model_versions: tuple[tuple[str, str], ...]
    alternative_snapshots_json: tuple[str, ...]


def replay_envelope(decision: CertifiedDecision) -> ReplayEnvelope:
    payload: dict[str, Any] = {
        "certificate_id": decision.certificate.certificate_id,
        "action_digest": decision.certificate.action_digest,
        "state_digest": decision.certificate.state_digest,
        "manifest_digest": decision.certificate.manifest_digest,
        "model_digest": decision.certificate.model_digest,
        "alternatives_digest": decision.certificate.alternatives_digest,
    }
    return ReplayEnvelope(
        replay_token="replay-" + sha256_hex(payload),
        certificate_id=decision.certificate.certificate_id,
        compiler_target=decision.compiler_target,
        requested_mode=decision.requested_mode,
        control_payload=decision.control_payload,
        state_snapshot_json=decision.state_snapshot_json,
        manifest_versions=decision.manifest_versions,
        model_versions=decision.model_versions,
        alternative_snapshots_json=decision.alternative_snapshots_json,
    )
