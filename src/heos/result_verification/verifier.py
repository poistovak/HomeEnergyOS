from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import (
    Observation,
    ResultExpectation,
    VerificationDecision,
    VerificationStatus,
)
from .policy import ResultVerificationPolicy


@dataclass(slots=True)
class ResultVerifier:
    policy: ResultVerificationPolicy = field(default_factory=ResultVerificationPolicy)

    def verify(
        self,
        expectation: ResultExpectation,
        observations: Iterable[Observation],
        *,
        attempts_used: int = 0,
        now: int | None = None,
    ) -> VerificationDecision:
        if attempts_used < 0:
            raise ValueError("attempts_used must be non-negative")

        supplied = tuple(observations)
        matching = tuple(
            sorted(
                (
                    observation
                    for observation in supplied
                    if observation.target == expectation.target
                    and observation.quality >= self.policy.minimum_quality
                ),
                key=lambda item: item.observed_at,
            )
        )

        status: VerificationStatus
        reasons: tuple[str, ...]
        observed_value: float | None = None
        absolute_error: float | None = None
        relative_error: float | None = None
        stable_samples = 0

        if not matching:
            if now is not None and now > expectation.deadline:
                status = VerificationStatus.TIMEOUT
                reasons = ("deadline passed without usable evidence",)
            else:
                status = VerificationStatus.UNKNOWN
                reasons = ("no usable observation for target",)
        else:
            latest = matching[-1]
            observed_value = latest.value
            absolute_error = abs(observed_value - expectation.expected_value)
            scale = max(abs(expectation.expected_value), 1.0)
            relative_error = absolute_error / scale

            stable_samples = self._trailing_stable_samples(expectation, matching)
            on_time = latest.observed_at <= expectation.deadline
            enough_samples = len(matching) >= expectation.minimum_samples
            exact_tolerance = expectation.effective_tolerance
            partial_tolerance = exact_tolerance * self.policy.partial_multiplier
            latest_within = absolute_error <= exact_tolerance
            latest_partial = absolute_error <= partial_tolerance

            if not on_time:
                status = VerificationStatus.TIMEOUT
                reasons = ("latest usable observation arrived after deadline",)
            elif latest_within and enough_samples and stable_samples >= expectation.stability_samples:
                status = VerificationStatus.SUCCESS
                reasons = ("expected result reached and remained stable",)
            elif latest_partial:
                status = VerificationStatus.PARTIAL
                reasons = ("result is near target but verification requirements are incomplete",)
            else:
                status = VerificationStatus.FAILED
                reasons = ("observed result is outside accepted tolerance",)

        action = self.policy.choose_action(
            status,
            attempts_used=attempts_used,
            rollback_supported=expectation.rollback_supported,
        )
        return VerificationDecision.create(
            command_id=expectation.command_id,
            target=expectation.target,
            status=status,
            action=action,
            expected_value=expectation.expected_value,
            observed_value=observed_value,
            absolute_error=absolute_error,
            relative_error=relative_error,
            stable_samples=stable_samples,
            evidence_count=len(matching),
            attempts_used=attempts_used,
            reasons=reasons,
            policy_version=self.policy.version,
        )

    @staticmethod
    def _trailing_stable_samples(
        expectation: ResultExpectation,
        observations: tuple[Observation, ...],
    ) -> int:
        tolerance = expectation.effective_tolerance
        count = 0
        for observation in reversed(observations):
            if abs(observation.value - expectation.expected_value) <= tolerance:
                count += 1
            else:
                break
        return count
