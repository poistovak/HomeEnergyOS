from __future__ import annotations

from .canonical import sha256_digest
from .models import RobustnessRun


def verify_run(run: RobustnessRun) -> bool:
    variants_payload = [item.to_dict() for item in run.variants]
    if sha256_digest(variants_payload) != run.certificate.variants_digest:
        return False
    payload = run.certificate.to_dict()
    expected = payload.pop("certificate_digest")
    payload.pop("certificate_id")
    payload.pop("metadata")
    return sha256_digest(payload) == expected
