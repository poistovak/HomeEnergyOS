from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from heos.feedback.models import OutcomeClassification, VersionStamp

from .models import HouseMemoryRecord, MemoryFingerprint, MemoryKind


def record_to_dict(record: HouseMemoryRecord) -> dict[str, Any]:
    return {
        "classification": record.classification.value,
        "explanation": record.explanation,
        "features": dict(record.features),
        "fingerprint": {
            "digest": record.fingerprint.digest,
            "dimensions": list(record.fingerprint.dimensions),
            "precision": record.fingerprint.precision,
        },
        "kind": record.kind.value,
        "occurred_at": record.occurred_at.isoformat(),
        "quality_score": record.quality_score,
        "record_id": record.record_id,
        "remembered_at": record.remembered_at.isoformat(),
        "source_experience_id": record.source_experience_id,
        "tags": list(record.tags),
        "targets": dict(record.targets),
        "versions": {
            "compiler_version": record.versions.compiler_version,
            "forecast_version": record.versions.forecast_version,
            "model_version": record.versions.model_version,
            "policy_version": record.versions.policy_version,
            "schema_version": record.versions.schema_version,
        },
    }


def record_from_dict(payload: Mapping[str, Any]) -> HouseMemoryRecord:
    from datetime import datetime

    versions_payload = payload["versions"]
    fingerprint_payload = payload["fingerprint"]
    return HouseMemoryRecord(
        record_id=str(payload["record_id"]),
        source_experience_id=str(payload["source_experience_id"]),
        remembered_at=datetime.fromisoformat(str(payload["remembered_at"])),
        occurred_at=datetime.fromisoformat(str(payload["occurred_at"])),
        features=dict(payload["features"]),
        targets=dict(payload["targets"]),
        quality_score=float(payload["quality_score"]),
        classification=OutcomeClassification(str(payload["classification"])),
        versions=VersionStamp(
            schema_version=str(versions_payload["schema_version"]),
            forecast_version=str(versions_payload["forecast_version"]),
            model_version=str(versions_payload["model_version"]),
            policy_version=str(versions_payload["policy_version"]),
            compiler_version=str(versions_payload["compiler_version"]),
        ),
        explanation=str(payload["explanation"]),
        fingerprint=MemoryFingerprint(
            digest=str(fingerprint_payload["digest"]),
            dimensions=tuple(fingerprint_payload["dimensions"]),
            precision=int(fingerprint_payload["precision"]),
        ),
        tags=tuple(payload.get("tags", ())),
        kind=MemoryKind(str(payload.get("kind", MemoryKind.EXPERIENCE.value))),
    )


def dumps_record(record: HouseMemoryRecord) -> str:
    return json.dumps(record_to_dict(record), sort_keys=True, separators=(",", ":"))


def loads_record(payload: str) -> HouseMemoryRecord:
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("memory record must be a JSON object")
    return record_from_dict(decoded)
