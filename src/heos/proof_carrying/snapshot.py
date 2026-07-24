from __future__ import annotations

from math import isfinite
from typing import Any

from .canonical import canonical_json


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _pairs(values: Any) -> list[list[str]]:
    return [[str(key), str(value)] for key, value in tuple(values or ())]


def release_snapshot(release: Any) -> dict[str, Any]:
    intent = getattr(release, "intent", None)
    intent_payload = None
    if intent is not None:
        intent_payload = {
            "intent_id": str(intent.intent_id),
            "source_decision_id": str(intent.source_decision_id),
            "candidate_id": str(intent.candidate_id),
            "requested_mode": _enum_value(intent.requested_mode),
            "created_at": intent.created_at.isoformat(),
            "not_after": intent.not_after.isoformat(),
            "compiler_target": str(intent.compiler_target),
            "control_payload": [
                [str(key), float(value)] for key, value in tuple(intent.control_payload)
            ],
            "metadata": _pairs(getattr(intent, "metadata", ())),
        }
    gates = [
        {
            "code": _enum_value(item.code),
            "passed": bool(item.passed),
            "critical": bool(item.critical),
            "detail": str(item.detail),
        }
        for item in tuple(release.gates)
    ]
    return {
        "release_id": str(release.release_id),
        "source_decision_id": str(release.source_decision_id),
        "evaluated_at": release.evaluated_at.isoformat(),
        "requested_mode": _enum_value(release.requested_mode),
        "status": _enum_value(release.status),
        "gates": gates,
        "policy_version": str(release.policy_version),
        "manifest_schema_version": str(release.manifest_schema_version),
        "intent": intent_payload,
        "explanation": str(release.explanation),
        "metadata": _pairs(getattr(release, "metadata", ())),
    }


def release_snapshot_json(release: Any) -> str:
    return canonical_json(release_snapshot(release))


def control_payload_is_finite(payload: Any) -> bool:
    values = tuple(payload or ())
    if not values:
        return False
    keys: list[str] = []
    for key, value in values:
        name = str(key).strip()
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        if not name or not isfinite(number):
            return False
        keys.append(name)
    return len(keys) == len(set(keys))
