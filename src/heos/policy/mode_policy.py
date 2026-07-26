from __future__ import annotations

from dataclasses import dataclass

from heos.release_gate import OperationMode, mode_rank


@dataclass(frozen=True, slots=True)
class ModePolicyResult:
    requested_mode: OperationMode
    effective_mode: OperationMode
    downgraded: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ModePolicy:
    maximum_mode: OperationMode = OperationMode.ADVISE

    def resolve(
        self,
        requested_mode: OperationMode,
    ) -> ModePolicyResult:
        requested = OperationMode(requested_mode)

        if mode_rank(requested) <= mode_rank(self.maximum_mode):
            return ModePolicyResult(
                requested_mode=requested,
                effective_mode=requested,
                downgraded=False,
                reason="requested mode is allowed",
            )

        return ModePolicyResult(
            requested_mode=requested,
            effective_mode=self.maximum_mode,
            downgraded=True,
            reason=(
                f"{requested.value} exceeds maximum "
                f"{self.maximum_mode.value}"
            ),
        )