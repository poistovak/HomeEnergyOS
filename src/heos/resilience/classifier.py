from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from .models import FaultSignal, Incident, IncidentClass


_CODE_MAP = {
    "stale": IncidentClass.DATA_STALE,
    "timeout": IncidentClass.DEVICE_UNAVAILABLE,
    "offline": IncidentClass.DEVICE_UNAVAILABLE,
    "constraint": IncidentClass.CONSTRAINT_VIOLATION,
    "drift": IncidentClass.MODEL_DRIFT,
    "mismatch": IncidentClass.EXECUTION_MISMATCH,
}


def classify_signal(signal: FaultSignal) -> IncidentClass:
    code = signal.code.lower()
    for token, incident_class in _CODE_MAP.items():
        if token in code:
            return incident_class
    return IncidentClass.UNKNOWN


def build_incident(signals: Iterable[FaultSignal]) -> Incident:
    ordered = tuple(
        sorted(signals, key=lambda item: (item.observed_at, item.source, item.code))
    )
    if not ordered:
        raise ValueError("at least one fault signal is required")

    classes = [classify_signal(signal) for signal in ordered]
    incident_class = max(
        classes,
        key=lambda cls: (
            sum(signal.severity for signal, found in zip(ordered, classes) if found is cls),
            cls.value,
        ),
    )
    severity = max(signal.severity for signal in ordered)
    opened_at = min(signal.observed_at for signal in ordered)
    payload = [
        {
            "source": signal.source,
            "code": signal.code,
            "severity": signal.severity,
            "observed_at": signal.observed_at,
            "details": dict(sorted(signal.details.items())),
        }
        for signal in ordered
    ]
    incident_id = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return Incident(
        incident_id=incident_id,
        incident_class=incident_class,
        severity=severity,
        signals=ordered,
        opened_at=opened_at,
    )


def incident_digest(incident: Incident) -> str:
    payload = {
        "incident_id": incident.incident_id,
        "incident_class": incident.incident_class.value,
        "severity": incident.severity,
        "opened_at": incident.opened_at,
        "signals": [
            {
                "source": signal.source,
                "code": signal.code,
                "severity": signal.severity,
                "observed_at": signal.observed_at,
                "details": dict(sorted(signal.details.items())),
            }
            for signal in incident.signals
        ],
    }
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
