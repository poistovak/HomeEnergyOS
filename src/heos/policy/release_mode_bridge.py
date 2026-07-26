from __future__ import annotations

from dataclasses import dataclass, replace

from heos.release_gate import OperationalRequest

from .mode_policy import ModePolicy, ModePolicyResult


@dataclass(frozen=True, slots=True)
class ReleaseModeBridge:
    policy: ModePolicy

    def apply(
        self,
        request: OperationalRequest,
    ) -> tuple[OperationalRequest, ModePolicyResult]:
        result = self.policy.resolve(
            request.requested_mode
        )

        mode_metadata = (
            ("requested_mode", result.requested_mode.value),
            ("effective_mode", result.effective_mode.value),
            ("mode_downgraded", str(result.downgraded).lower()),
            ("mode_policy_reason", result.reason),
        )

        effective_request = replace(
            request,
            requested_mode=result.effective_mode,
            metadata=(
                *request.metadata,
                *mode_metadata,
            ),
        )

        return effective_request, result