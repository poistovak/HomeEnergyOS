from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from math import isfinite
from typing import Any


def to_primitive(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("non-finite floats cannot be canonicalized")
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetimes must be timezone-aware")
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, Enum):
        return to_primitive(value.value)
    if is_dataclass(value):
        return to_primitive(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [to_primitive(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [to_primitive(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
    if hasattr(value, "__dict__"):
        return to_primitive(vars(value))
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        to_primitive(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_hex(value: Any) -> str:
    payload = value if isinstance(value, str) else canonical_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_versions(values: Any) -> tuple[tuple[str, str], ...]:
    if isinstance(values, dict):
        iterator = values.items()
    else:
        iterator = values
    normalized = tuple(sorted((str(key).strip(), str(version).strip()) for key, version in iterator))
    if any(not key or not version for key, version in normalized):
        raise ValueError("version names and values must not be empty")
    keys = [key for key, _ in normalized]
    if len(keys) != len(set(keys)):
        raise ValueError("version names must be unique")
    return normalized
