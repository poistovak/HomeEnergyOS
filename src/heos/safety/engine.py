"""Deterministic safety-rule aggregation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from .context import SafetyContext
from .models import (
    SafetyFinding,
    SafetyReport,
    SafetyVerdict,
)
from .rules import (
    GridImportLimitRule,
    KernelHealthRule,
    ManualLockRule,
    RequiredVerificationRule,
    SafetyRule,
)


class SafetyEngine:
    """Search for reasons why a plan must not execute."""

    _priority: ClassVar[dict[SafetyVerdict, int]] = {
        SafetyVerdict.ALLOW: 0,
        SafetyVerdict.RETRY_LATER: 1,
        SafetyVerdict.DENY: 2,
    }

    def __init__(
        self,
        rules: Iterable[SafetyRule] | None = None,
    ) -> None:
        self._rules = tuple(
            rules
            if rules is not None
            else (
                KernelHealthRule(),
                ManualLockRule(),
                GridImportLimitRule(),
                RequiredVerificationRule(),
            )
        )

        if not self._rules:
            raise ValueError(
                "SafetyEngine requires at least one safety rule"
            )

    def evaluate(self, context: SafetyContext) -> SafetyReport:
        findings: tuple[SafetyFinding, ...] = tuple(
            rule.evaluate(context)
            for rule in self._rules
        )

        verdict = max(
            (finding.verdict for finding in findings),
            key=self._priority.__getitem__,
        )

        return SafetyReport(
            verdict=verdict,
            findings=findings,
        )