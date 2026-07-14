"""Safety verdicts and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SafetyVerdict(StrEnum):
    ALLOW = "allow"
    RETRY_LATER = "retry_later"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class SafetyFinding:
    rule_id: str
    verdict: SafetyVerdict
    reason: str


@dataclass(frozen=True, slots=True)
class SafetyReport:
    verdict: SafetyVerdict
    findings: tuple[SafetyFinding, ...]
    evaluated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def allowed(self) -> bool:
        return self.verdict is SafetyVerdict.ALLOW

    @property
    def denied(self) -> bool:
        return self.verdict is SafetyVerdict.DENY

    @property
    def reasons(self) -> tuple[str, ...]:
        return tuple(
            finding.reason
            for finding in self.findings
            if finding.verdict is not SafetyVerdict.ALLOW
        )
