from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256


class OutcomeStatus(str, Enum):
    VERIFIED = "verified"
    DEGRADED = "degraded"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class ExpectedOutcome:
    command_id: str
    incident_id: str
    metric: str
    target_min: float
    target_max: float
    deadline: int
    source_digest: str

    def __post_init__(self) -> None:
        if not all((self.command_id.strip(), self.incident_id.strip(), self.metric.strip(), self.source_digest.strip())):
            raise ValueError("expected outcome fields must not be empty")
        if self.target_min > self.target_max:
            raise ValueError("target_min must not exceed target_max")
        if self.deadline < 0:
            raise ValueError("deadline must be non-negative")


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    command_id: str
    observed_at: int
    values: Mapping[str, float]
    attempts_used: int
    executor: str

    def __post_init__(self) -> None:
        if not self.command_id.strip() or not self.executor.strip():
            raise ValueError("command_id and executor must not be empty")
        if self.observed_at < 0 or self.attempts_used < 0:
            raise ValueError("evidence counters must be non-negative")


@dataclass(frozen=True, slots=True)
class VerificationResult:
    result_id: str
    command_id: str
    incident_id: str
    status: OutcomeStatus
    observed_value: float | None
    deviation: float | None
    retry_recommended: bool
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.result_id.strip() or not self.command_id.strip():
            raise ValueError("result_id and command_id must not be empty")
        if not self.reasons:
            raise ValueError("reasons must not be empty")
        if self.status is OutcomeStatus.VERIFIED and self.retry_recommended:
            raise ValueError("verified result cannot recommend retry")


@dataclass(frozen=True, slots=True)
class OutcomeCertificate:
    result: VerificationResult
    expectation_digest: str
    evidence_digest: str
    policy_version: str
    previous_digest: str | None
    digest: str

    @staticmethod
    def canonical_payload(result: VerificationResult, expectation_digest: str, evidence_digest: str, policy_version: str, previous_digest: str | None) -> str:
        return json.dumps(
            {
                "result": asdict(result),
                "expectation_digest": expectation_digest,
                "evidence_digest": evidence_digest,
                "policy_version": policy_version,
                "previous_digest": previous_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @classmethod
    def issue(cls, *, result: VerificationResult, expectation_digest: str, evidence_digest: str, policy_version: str, previous_digest: str | None = None) -> OutcomeCertificate:
        payload = cls.canonical_payload(result, expectation_digest, evidence_digest, policy_version, previous_digest)
        return cls(result, expectation_digest, evidence_digest, policy_version, previous_digest, sha256(payload.encode()).hexdigest())

    def verify(self) -> bool:
        payload = self.canonical_payload(self.result, self.expectation_digest, self.evidence_digest, self.policy_version, self.previous_digest)
        return sha256(payload.encode()).hexdigest() == self.digest

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)
