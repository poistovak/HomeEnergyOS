from __future__ import annotations

import json
from typing import Any

from .canonical import canonical_json
from .models import ProofPolicy


def proof_policy_to_dict(policy: ProofPolicy) -> dict[str, Any]:
    return {
        "allowed_compiler_targets": list(policy.allowed_compiler_targets),
        "required_model_components": list(policy.required_model_components),
        "require_all_release_gates_passed": policy.require_all_release_gates_passed,
        "require_chain_link": policy.require_chain_link,
        "maximum_clock_skew_seconds": policy.maximum_clock_skew.total_seconds(),
        "version": policy.version,
    }


def proof_policy_json(policy: ProofPolicy) -> str:
    return canonical_json(proof_policy_to_dict(policy))


def parse_policy_json(value: str) -> dict[str, Any]:
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("proof policy JSON must contain an object")
    return payload
