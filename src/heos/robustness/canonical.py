from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import NAMESPACE_URL, uuid5


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_digest(value: Any) -> str:
    payload = canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def stable_id(namespace: str, value: Any) -> str:
    return str(uuid5(NAMESPACE_URL, f"{namespace}:{canonical_json(value)}"))
