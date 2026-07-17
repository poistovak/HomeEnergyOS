from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from .models import ExecutionEvidence, ExpectedOutcome, OutcomeStatus, VerificationResult


@dataclass(frozen=True, slots=True)
class VerificationPolicy:
    version: str = "27.0.0"
    degraded_tolerance: float = 0.10
    retry_limit: int = 3

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("version must not be empty")
        if self.degraded_tolerance < 0:
            raise ValueError("degraded_tolerance must be non-negative")
        if self.retry_limit < 0:
            raise ValueError("retry_limit must be non-negative")

    def evaluate(self, expected: ExpectedOutcome, evidence: ExecutionEvidence) -> VerificationResult:
        reasons: list[str] = []
        value = evidence.values.get(expected.metric)
        deviation: float | None = None
        retry = False

        if evidence.command_id != expected.command_id:
            status = OutcomeStatus.FAILED
            reasons.append("evidence command mismatch")
        elif evidence.observed_at > expected.deadline:
            status = OutcomeStatus.FAILED
            reasons.append("evidence arrived after deadline")
        elif value is None:
            status = OutcomeStatus.INCONCLUSIVE
            retry = evidence.attempts_used < self.retry_limit
            reasons.append("required metric missing")
        elif expected.target_min <= value <= expected.target_max:
            status = OutcomeStatus.VERIFIED
            deviation = 0.0
            reasons.append("observed value is inside target range")
        else:
            distance = expected.target_min - value if value < expected.target_min else value - expected.target_max
            scale = max(abs(expected.target_min), abs(expected.target_max), 1.0)
            deviation = distance / scale
            if deviation <= self.degraded_tolerance:
                status = OutcomeStatus.DEGRADED
                retry = evidence.attempts_used < self.retry_limit
                reasons.append("observed value is outside target but within degraded tolerance")
            else:
                status = OutcomeStatus.FAILED
                retry = evidence.attempts_used < self.retry_limit
                reasons.append("observed value exceeds degraded tolerance")

        payload = {
            "expected": asdict(expected),
            "evidence": asdict(evidence),
            "status": status.value,
            "policy_version": self.version,
        }
        result_id = "out-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:20]
        return VerificationResult(
            result_id=result_id,
            command_id=expected.command_id,
            incident_id=expected.incident_id,
            status=status,
            observed_value=value,
            deviation=deviation,
            retry_recommended=retry,
            reasons=tuple(reasons),
        )
