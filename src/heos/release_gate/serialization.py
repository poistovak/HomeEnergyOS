from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .models import (
    ExecutionIntent,
    GateCode,
    GateResult,
    OperationMode,
    ReleaseDecision,
    ReleaseStatus,
)


def release_decision_to_dict(decision: ReleaseDecision) -> dict[str, Any]:
    intent = None
    if decision.intent is not None:
        intent = {
            "intent_id": decision.intent.intent_id,
            "source_decision_id": decision.intent.source_decision_id,
            "candidate_id": decision.intent.candidate_id,
            "requested_mode": decision.intent.requested_mode.value,
            "created_at": decision.intent.created_at.isoformat(),
            "not_after": decision.intent.not_after.isoformat(),
            "compiler_target": decision.intent.compiler_target,
            "control_payload": [list(item) for item in decision.intent.control_payload],
            "metadata": [list(item) for item in decision.intent.metadata],
        }

    return {
        "release_id": decision.release_id,
        "source_decision_id": decision.source_decision_id,
        "evaluated_at": decision.evaluated_at.isoformat(),
        "requested_mode": decision.requested_mode.value,
        "status": decision.status.value,
        "gates": [
            {
                "code": item.code.value,
                "passed": item.passed,
                "critical": item.critical,
                "detail": item.detail,
            }
            for item in decision.gates
        ],
        "policy_version": decision.policy_version,
        "manifest_schema_version": decision.manifest_schema_version,
        "intent": intent,
        "explanation": decision.explanation,
        "metadata": [list(item) for item in decision.metadata],
    }


def release_decision_from_dict(payload: dict[str, Any]) -> ReleaseDecision:
    raw_intent = payload.get("intent")
    intent = None
    if raw_intent is not None:
        intent = ExecutionIntent(
            intent_id=raw_intent["intent_id"],
            source_decision_id=raw_intent["source_decision_id"],
            candidate_id=raw_intent["candidate_id"],
            requested_mode=OperationMode(raw_intent["requested_mode"]),
            created_at=datetime.fromisoformat(raw_intent["created_at"]),
            not_after=datetime.fromisoformat(raw_intent["not_after"]),
            compiler_target=raw_intent["compiler_target"],
            control_payload=tuple(
                (str(key), float(value))
                for key, value in raw_intent["control_payload"]
            ),
            metadata=tuple(
                (str(key), str(value)) for key, value in raw_intent.get("metadata", ())
            ),
        )

    return ReleaseDecision(
        release_id=payload["release_id"],
        source_decision_id=payload["source_decision_id"],
        evaluated_at=datetime.fromisoformat(payload["evaluated_at"]),
        requested_mode=OperationMode(payload["requested_mode"]),
        status=ReleaseStatus(payload["status"]),
        gates=tuple(
            GateResult(
                code=GateCode(item["code"]),
                passed=bool(item["passed"]),
                critical=bool(item["critical"]),
                detail=item["detail"],
            )
            for item in payload["gates"]
        ),
        policy_version=payload["policy_version"],
        manifest_schema_version=payload["manifest_schema_version"],
        intent=intent,
        explanation=payload["explanation"],
        metadata=tuple(
            (str(key), str(value)) for key, value in payload.get("metadata", ())
        ),
    )


def dumps_release_decision(decision: ReleaseDecision) -> str:
    return json.dumps(
        release_decision_to_dict(decision),
        sort_keys=True,
        separators=(",", ":"),
    )


def loads_release_decision(value: str) -> ReleaseDecision:
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise TypeError("release decision JSON must contain an object")
    return release_decision_from_dict(payload)

