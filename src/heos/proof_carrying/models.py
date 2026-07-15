from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite


def _text(value: str, name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


def _digest(value: str, name: str) -> str:
    normalized = _text(value, name).lower()
    if len(normalized) != 64 or any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    return normalized


def _pairs(values: tuple[tuple[str, str], ...], name: str) -> tuple[tuple[str, str], ...]:
    normalized = tuple(sorted((_text(key, f"{name} key"), _text(value, f"{name} value")) for key, value in values))
    keys = [key for key, _ in normalized]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{name} keys must be unique")
    return normalized


def _control_pairs(values: tuple[tuple[str, float], ...]) -> tuple[tuple[str, float], ...]:
    normalized: list[tuple[str, float]] = []
    for key, value in values:
        name = _text(key, "control key")
        number = float(value)
        if not isfinite(number):
            raise ValueError(f"control value {name} must be finite")
        normalized.append((name, number))
    result = tuple(sorted(normalized))
    keys = [key for key, _ in result]
    if not result:
        raise ValueError("control_payload must not be empty")
    if len(keys) != len(set(keys)):
        raise ValueError("control keys must be unique")
    return result


class HashAlgorithm(StrEnum):
    SHA256 = "sha256"


class ClaimCode(StrEnum):
    RELEASE_STATUS = "release_status"
    INTENT_PRESENT = "intent_present"
    SOURCE_BOUND = "source_bound"
    ALL_GATES_PASSED = "all_gates_passed"
    COMPILER_TARGET_ALLOWED = "compiler_target_allowed"
    INTENT_WINDOW_VALID = "intent_window_valid"
    PAYLOAD_FINITE = "payload_finite"
    MANIFEST_BOUND = "manifest_bound"
    MODEL_VERSIONS_BOUND = "model_versions_bound"
    STATE_BOUND = "state_bound"
    POLICY_BOUND = "policy_bound"
    ALTERNATIVES_BOUND = "alternatives_bound"
    CHAIN_BOUND = "chain_bound"


class VerificationCode(StrEnum):
    CERTIFICATE_ID = "certificate_id"
    RELEASE_SNAPSHOT = "release_snapshot"
    STATE_SNAPSHOT = "state_snapshot"
    MANIFEST = "manifest"
    MODEL_VERSIONS = "model_versions"
    POLICY = "policy"
    ACTION = "action"
    ALTERNATIVES = "alternatives"
    CLAIMS = "claims"
    RELEASE_STATUS = "release_status"
    INTENT = "intent"
    SOURCE_BINDING = "source_binding"
    GATES = "gates"
    COMPILER_TARGET = "compiler_target"
    VALIDITY_WINDOW = "validity_window"
    CHAIN_LINK = "chain_link"
    SCHEMA = "schema"


@dataclass(frozen=True, slots=True)
class EvidenceClaim:
    code: ClaimCode
    passed: bool
    critical: bool
    detail: str
    evidence_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", ClaimCode(self.code))
        object.__setattr__(self, "detail", _text(self.detail, "detail"))
        object.__setattr__(self, "evidence_hash", _digest(self.evidence_hash, "evidence_hash"))


@dataclass(frozen=True, slots=True)
class ProofPolicy:
    allowed_compiler_targets: tuple[str, ...] = ("heos.decision_compiler",)
    required_model_components: tuple[str, ...] = (
        "digital_twin",
        "calibration",
        "strategy",
    )
    require_all_release_gates_passed: bool = True
    require_chain_link: bool = False
    maximum_clock_skew: timedelta = timedelta(seconds=30)
    version: str = "proof-policy-1"

    def __post_init__(self) -> None:
        targets = tuple(sorted({_text(item, "compiler target") for item in self.allowed_compiler_targets}))
        if not targets:
            raise ValueError("allowed_compiler_targets must not be empty")
        components = tuple(sorted({_text(item, "model component") for item in self.required_model_components}))
        if not components:
            raise ValueError("required_model_components must not be empty")
        if self.maximum_clock_skew.total_seconds() < 0:
            raise ValueError("maximum_clock_skew must be non-negative")
        object.__setattr__(self, "allowed_compiler_targets", targets)
        object.__setattr__(self, "required_model_components", components)
        object.__setattr__(self, "version", _text(self.version, "version"))


@dataclass(frozen=True, slots=True)
class DecisionCertificate:
    certificate_id: str
    release_id: str
    source_decision_id: str
    intent_id: str
    issued_at: datetime
    expires_at: datetime
    action_digest: str
    release_snapshot_digest: str
    state_digest: str
    manifest_digest: str
    model_digest: str
    policy_digest: str
    alternatives_digest: str
    previous_certificate_hash: str | None
    claims: tuple[EvidenceClaim, ...]
    proof_policy_version: str
    schema_version: str = "heos-proof-carrying-decision-1"
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "certificate_id", _text(self.certificate_id, "certificate_id"))
        object.__setattr__(self, "release_id", _text(self.release_id, "release_id"))
        object.__setattr__(self, "source_decision_id", _text(self.source_decision_id, "source_decision_id"))
        object.__setattr__(self, "intent_id", _text(self.intent_id, "intent_id"))
        issued = _aware(self.issued_at, "issued_at")
        expires = _aware(self.expires_at, "expires_at")
        if expires <= issued:
            raise ValueError("expires_at must be after issued_at")
        object.__setattr__(self, "issued_at", issued)
        object.__setattr__(self, "expires_at", expires)
        for name in (
            "action_digest",
            "release_snapshot_digest",
            "state_digest",
            "manifest_digest",
            "model_digest",
            "policy_digest",
            "alternatives_digest",
        ):
            object.__setattr__(self, name, _digest(getattr(self, name), name))
        if self.previous_certificate_hash is not None:
            object.__setattr__(
                self,
                "previous_certificate_hash",
                _digest(self.previous_certificate_hash, "previous_certificate_hash"),
            )
        claims = tuple(self.claims)
        if not claims:
            raise ValueError("claims must not be empty")
        codes = [item.code for item in claims]
        if len(codes) != len(set(codes)):
            raise ValueError("claim codes must be unique")
        object.__setattr__(self, "claims", tuple(sorted(claims, key=lambda item: item.code.value)))
        object.__setattr__(self, "proof_policy_version", _text(self.proof_policy_version, "proof_policy_version"))
        object.__setattr__(self, "schema_version", _text(self.schema_version, "schema_version"))
        object.__setattr__(self, "hash_algorithm", HashAlgorithm(self.hash_algorithm))
        object.__setattr__(self, "metadata", _pairs(tuple(self.metadata), "metadata"))

    @property
    def all_claims_passed(self) -> bool:
        return all(item.passed for item in self.claims)

    @property
    def failed_claims(self) -> tuple[EvidenceClaim, ...]:
        return tuple(item for item in self.claims if not item.passed)


@dataclass(frozen=True, slots=True)
class CertifiedDecision:
    certificate: DecisionCertificate
    release_snapshot_json: str
    state_snapshot_json: str
    proof_policy_json: str
    compiler_target: str
    requested_mode: str
    control_payload: tuple[tuple[str, float], ...]
    manifest_versions: tuple[tuple[str, str], ...]
    model_versions: tuple[tuple[str, str], ...]
    alternative_snapshots_json: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_snapshot_json", _text(self.release_snapshot_json, "release_snapshot_json"))
        object.__setattr__(self, "state_snapshot_json", _text(self.state_snapshot_json, "state_snapshot_json"))
        object.__setattr__(self, "proof_policy_json", _text(self.proof_policy_json, "proof_policy_json"))
        object.__setattr__(self, "compiler_target", _text(self.compiler_target, "compiler_target"))
        object.__setattr__(self, "requested_mode", _text(self.requested_mode, "requested_mode"))
        object.__setattr__(self, "control_payload", _control_pairs(tuple(self.control_payload)))
        object.__setattr__(self, "manifest_versions", _pairs(tuple(self.manifest_versions), "manifest_versions"))
        object.__setattr__(self, "model_versions", _pairs(tuple(self.model_versions), "model_versions"))
        object.__setattr__(
            self,
            "alternative_snapshots_json",
            tuple(_text(item, "alternative snapshot") for item in self.alternative_snapshots_json),
        )


@dataclass(frozen=True, slots=True)
class VerificationIssue:
    code: VerificationCode
    critical: bool
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", VerificationCode(self.code))
        object.__setattr__(self, "detail", _text(self.detail, "detail"))


@dataclass(frozen=True, slots=True)
class VerificationReport:
    certificate_id: str
    verified_at: datetime
    valid: bool
    issues: tuple[VerificationIssue, ...]
    recomputed_certificate_id: str
    checked_claims: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "certificate_id", _text(self.certificate_id, "certificate_id"))
        object.__setattr__(self, "verified_at", _aware(self.verified_at, "verified_at"))
        object.__setattr__(
            self,
            "recomputed_certificate_id",
            _text(self.recomputed_certificate_id, "recomputed_certificate_id"),
        )
        if self.checked_claims < 0:
            raise ValueError("checked_claims must be non-negative")
        issues = tuple(self.issues)
        object.__setattr__(self, "issues", issues)
        if self.valid != (not any(item.critical for item in issues)):
            raise ValueError("valid must reflect critical verification issues")


@dataclass(frozen=True, slots=True)
class ChainAuditIssue:
    index: int
    detail: str

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("index must be non-negative")
        object.__setattr__(self, "detail", _text(self.detail, "detail"))


@dataclass(frozen=True, slots=True)
class ChainAuditReport:
    valid: bool
    length: int
    head_hash: str | None
    issues: tuple[ChainAuditIssue, ...] = ()

    def __post_init__(self) -> None:
        if self.length < 0:
            raise ValueError("length must be non-negative")
        if self.head_hash is not None:
            object.__setattr__(self, "head_hash", _digest(self.head_hash, "head_hash"))
        issues = tuple(self.issues)
        object.__setattr__(self, "issues", issues)
        if self.valid != (not issues):
            raise ValueError("valid must reflect chain audit issues")
