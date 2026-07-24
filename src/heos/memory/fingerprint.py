from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from heos.feedback.models import OutcomeClassification, VersionStamp

from .models import MemoryFingerprint


def _quantize(value: float, precision: int) -> float:
    rounded = round(float(value), precision)
    return 0.0 if rounded == 0.0 else rounded


def build_fingerprint(
    *,
    features: Mapping[str, float],
    targets: Mapping[str, float],
    classification: OutcomeClassification,
    versions: VersionStamp,
    precision: int = 3,
) -> MemoryFingerprint:
    if precision < 0 or precision > 12:
        raise ValueError("precision must be between 0 and 12")

    canonical = {
        "classification": classification.value,
        "features": {
            str(key): _quantize(value, precision)
            for key, value in sorted(features.items())
        },
        "targets": {
            str(key): _quantize(value, precision)
            for key, value in sorted(targets.items())
        },
        "versions": {
            "compiler": versions.compiler_version,
            "forecast": versions.forecast_version,
            "model": versions.model_version,
            "policy": versions.policy_version,
            "schema": versions.schema_version,
        },
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    dimensions = tuple(
        [f"feature:{key}" for key in sorted(features)]
        + [f"target:{key}" for key in sorted(targets)]
    )
    return MemoryFingerprint(
        digest=hashlib.sha256(encoded).hexdigest(),
        dimensions=dimensions,
        precision=precision,
    )


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    score: float
    overlap: float
    matched_dimensions: tuple[str, ...]


def numeric_similarity(
    query: Mapping[str, float],
    candidate: Mapping[str, float],
) -> SimilarityResult:
    query_keys = set(query)
    candidate_keys = set(candidate)
    union = query_keys | candidate_keys
    overlap_keys = tuple(sorted(query_keys & candidate_keys))
    if not union or not overlap_keys:
        return SimilarityResult(score=0.0, overlap=0.0, matched_dimensions=())

    components: list[float] = []
    for key in overlap_keys:
        left = float(query[key])
        right = float(candidate[key])
        scale = max(abs(left), abs(right), 1.0)
        components.append(max(0.0, 1.0 - abs(left - right) / scale))

    overlap = len(overlap_keys) / len(union)
    score = (sum(components) / len(components)) * overlap
    return SimilarityResult(
        score=max(0.0, min(1.0, score)),
        overlap=overlap,
        matched_dimensions=overlap_keys,
    )
