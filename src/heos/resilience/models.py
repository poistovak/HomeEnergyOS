from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
from typing import Any


class IncidentClass(str, Enum):
    DATA_STALE = "data_stale"
    DEVICE_UNAVAILABLE = "device_unavailable"
    CONSTRAINT_VIOLATION = "constraint_violation"
    MODEL_DRIFT = "model_drift"
    EXECUTION_MISMATCH = "execution_mismatch"
    UNKNOWN = "unknown"


class RecoveryMode(str, Enum):
    CONTINUE = "continue"
    DEGRADE = "degrade"
    HOLD = "hold"
    FALLBACK = "fallback"
    SAFE_STOP = "safe_stop"


class RecoveryStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class FaultSignal:
    source: str
    code: str
    severity: int
    observed_at: int
    details: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if not self.code.strip():
            raise ValueError("code must not be empty")
        if not 0 <= self.severity <= 100:
            raise ValueError("severity must be between 0 and 100")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")


@dataclass(frozen=True, slots=True)
class Incident:
    incident_id: str
    incident_class: IncidentClass
    severity: int
    signals: tuple[FaultSignal, ...]
    opened_at: int

    def __post_init__(self) -> None:
        if not self.incident_id.strip():
            raise ValueError("incident_id must not be empty")
        if not self.signals:
            raise ValueError("incident must contain at least one signal")
        if not 0 <= self.severity <= 100:
            raise ValueError("severity must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    incident_id: str
    mode: RecoveryMode
    status: RecoveryStatus
    fallback_strategy: str | None
    reasons: tuple[str, ...]
    valid_until: int

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("recovery decision must contain reasons")
        if self.valid_until < 0:
            raise ValueError("valid_until must be non-negative")
        if self.mode is RecoveryMode.FALLBACK and not self.fallback_strategy:
            raise ValueError("fallback mode requires fallback_strategy")
        if self.status is RecoveryStatus.BLOCKED and self.mode not in {
            RecoveryMode.HOLD,
            RecoveryMode.SAFE_STOP,
        }:
            raise ValueError("blocked decisions must hold or safe-stop")


@dataclass(frozen=True, slots=True)
class RecoveryCertificate:
    decision: RecoveryDecision
    incident_digest: str
    policy_version: str
    previous_digest: str | None
    digest: str

    @staticmethod
    def canonical_payload(
        decision: RecoveryDecision,
        incident_digest: str,
        policy_version: str,
        previous_digest: str | None,
    ) -> str:
        payload = {
            "decision": asdict(decision),
            "incident_digest": incident_digest,
            "policy_version": policy_version,
            "previous_digest": previous_digest,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)

    @classmethod
    def issue(
        cls,
        *,
        decision: RecoveryDecision,
        incident_digest: str,
        policy_version: str,
        previous_digest: str | None = None,
    ) -> RecoveryCertificate:
        payload = cls.canonical_payload(
            decision, incident_digest, policy_version, previous_digest
        )
        digest = sha256(payload.encode("utf-8")).hexdigest()
        return cls(
            decision=decision,
            incident_digest=incident_digest,
            policy_version=policy_version,
            previous_digest=previous_digest,
            digest=digest,
        )

    def verify(self) -> bool:
        payload = self.canonical_payload(
            self.decision,
            self.incident_digest,
            self.policy_version,
            self.previous_digest,
        )
        return sha256(payload.encode("utf-8")).hexdigest() == self.digest

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)
