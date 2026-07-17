from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .models import Incident, IncidentClass, RecoveryDecision, RecoveryMode, RecoveryStatus


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    version: str = "24.0.0"
    hold_threshold: int = 70
    safe_stop_threshold: int = 90
    decision_ttl: int = 300
    fallback_by_class: Mapping[IncidentClass, str] | None = None

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("version must not be empty")
        if not 0 <= self.hold_threshold <= self.safe_stop_threshold <= 100:
            raise ValueError("invalid recovery thresholds")
        if self.decision_ttl <= 0:
            raise ValueError("decision_ttl must be positive")

    def evaluate(self, incident: Incident, *, now: int) -> RecoveryDecision:
        fallbacks = self.fallback_by_class or {
            IncidentClass.DATA_STALE: "last_known_safe_plan",
            IncidentClass.DEVICE_UNAVAILABLE: "device_isolation_plan",
            IncidentClass.CONSTRAINT_VIOLATION: "constraint_safe_plan",
            IncidentClass.MODEL_DRIFT: "conservative_static_plan",
            IncidentClass.EXECUTION_MISMATCH: "verified_hold_plan",
        }

        if incident.severity >= self.safe_stop_threshold:
            return RecoveryDecision(
                incident_id=incident.incident_id,
                mode=RecoveryMode.SAFE_STOP,
                status=RecoveryStatus.BLOCKED,
                fallback_strategy=None,
                reasons=("critical severity", incident.incident_class.value),
                valid_until=now + self.decision_ttl,
            )

        if incident.severity >= self.hold_threshold:
            return RecoveryDecision(
                incident_id=incident.incident_id,
                mode=RecoveryMode.HOLD,
                status=RecoveryStatus.BLOCKED,
                fallback_strategy=None,
                reasons=("high severity", incident.incident_class.value),
                valid_until=now + self.decision_ttl,
            )

        fallback = fallbacks.get(incident.incident_class)
        if fallback:
            return RecoveryDecision(
                incident_id=incident.incident_id,
                mode=RecoveryMode.FALLBACK,
                status=RecoveryStatus.READY,
                fallback_strategy=fallback,
                reasons=("bounded degradation", incident.incident_class.value),
                valid_until=now + self.decision_ttl,
            )

        return RecoveryDecision(
            incident_id=incident.incident_id,
            mode=RecoveryMode.DEGRADE,
            status=RecoveryStatus.READY,
            fallback_strategy=None,
            reasons=("unknown incident class",),
            valid_until=now + self.decision_ttl,
        )
