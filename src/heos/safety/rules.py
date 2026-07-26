"""Built-in HEOS safety rules."""

from __future__ import annotations

from typing import ClassVar, Protocol

from heos.compiler.execution_step import StepType
from heos.kernel import KernelHealth

from .context import SafetyContext
from .models import SafetyFinding, SafetyVerdict


class SafetyRule(Protocol):
    rule_id: str

    def evaluate(self, context: SafetyContext) -> SafetyFinding:
        """Evaluate one plan without producing side effects."""


class KernelHealthRule:
    rule_id = "kernel_health"

    def evaluate(self, context: SafetyContext) -> SafetyFinding:
        if context.kernel.health is KernelHealth.BLOCKED:
            return SafetyFinding(
                rule_id=self.rule_id,
                verdict=SafetyVerdict.DENY,
                reason="Energy Kernel is blocked.",
            )

        if context.kernel.health is KernelHealth.DEGRADED:
            return SafetyFinding(
                rule_id=self.rule_id,
                verdict=SafetyVerdict.RETRY_LATER,
                reason="Energy Kernel is degraded.",
            )

        return SafetyFinding(
            rule_id=self.rule_id,
            verdict=SafetyVerdict.ALLOW,
            reason="Energy Kernel is ready.",
        )


class ManualLockRule:
    rule_id = "manual_lock"

    def evaluate(self, context: SafetyContext) -> SafetyFinding:
        if context.manual_lock:
            return SafetyFinding(
                rule_id=self.rule_id,
                verdict=SafetyVerdict.DENY,
                reason="Manual execution lock is active.",
            )

        return SafetyFinding(
            rule_id=self.rule_id,
            verdict=SafetyVerdict.ALLOW,
            reason="Manual execution lock is inactive.",
        )


class GridImportLimitRule:
    rule_id = "grid_import_limit"

    def evaluate(self, context: SafetyContext) -> SafetyFinding:
        limit = context.maximum_grid_import_w

        if limit is None:
            return SafetyFinding(
                rule_id=self.rule_id,
                verdict=SafetyVerdict.ALLOW,
                reason="No grid-import safety limit configured.",
            )

        if context.projected_grid_import_w > limit:
            return SafetyFinding(
                rule_id=self.rule_id,
                verdict=SafetyVerdict.DENY,
                reason=(
                    "Projected grid import "
                    f"{context.projected_grid_import_w:.0f} W exceeds "
                    f"limit {limit:.0f} W."
                ),
            )

        return SafetyFinding(
            rule_id=self.rule_id,
            verdict=SafetyVerdict.ALLOW,
            reason="Projected grid import is within the limit.",
        )


class RequiredVerificationRule:
    """Require a VERIFY step after every state-changing step."""

    rule_id = "required_verification"

    _write_steps: ClassVar[set[StepType]] = {
        StepType.SET_CURRENT,
    }

    def evaluate(self, context: SafetyContext) -> SafetyFinding:
        steps = context.plan.steps

        for index, step in enumerate(steps):
            if step.step_type not in self._write_steps:
                continue

            if index + 1 >= len(steps):
                return SafetyFinding(
                    rule_id=self.rule_id,
                    verdict=SafetyVerdict.DENY,
                    reason=(
                        f"Step {index} changes state without a following "
                        "verification step."
                    ),
                )

            next_step = steps[index + 1]
            if next_step.step_type is not StepType.VERIFY:
                return SafetyFinding(
                    rule_id=self.rule_id,
                    verdict=SafetyVerdict.DENY,
                    reason=(
                        f"Step {index} changes state but step "
                        f"{index + 1} is not VERIFY."
                    ),
                )

        return SafetyFinding(
            rule_id=self.rule_id,
            verdict=SafetyVerdict.ALLOW,
            reason="Every state-changing step is followed by verification.",
        )
