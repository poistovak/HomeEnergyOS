from __future__ import annotations

from dataclasses import dataclass

from heos.policy.mode_policy import ModePolicy, ModePolicyResult
from heos.policy.release_mode_bridge import ReleaseModeBridge
from heos.release_gate import (
    OperationalReleaseGate,
    OperationalRequest,
    ReleaseDecision,
)


@dataclass(frozen=True, slots=True)
class AutonomyControlResult:
    original_request: OperationalRequest
    effective_request: OperationalRequest
    mode_result: ModePolicyResult
    release: ReleaseDecision

    @property
    def released(self) -> bool:
        return self.release.released

    @property
    def downgraded(self) -> bool:
        return self.mode_result.downgraded


class AutonomyController:
    def __init__(
        self,
        *,
        mode_policy: ModePolicy,
        release_gate: OperationalReleaseGate,
    ) -> None:
        self._bridge = ReleaseModeBridge(
            policy=mode_policy,
        )
        self._release_gate = release_gate

    def evaluate(
        self,
        request: OperationalRequest,
    ) -> AutonomyControlResult:
        effective_request, mode_result = self._bridge.apply(
            request
        )

        release = self._release_gate.review(
            effective_request
        )

        return AutonomyControlResult(
            original_request=request,
            effective_request=effective_request,
            mode_result=mode_result,
            release=release,
        )