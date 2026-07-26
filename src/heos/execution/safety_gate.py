from __future__ import annotations

from dataclasses import dataclass

from heos.safety import SafetyContext, SafetyEngine, SafetyReport

from .models import RuntimeReport
from .runtime import ExecutionRuntime


@dataclass(frozen=True, slots=True)
class SafetyExecutionResult:
    safety: SafetyReport
    runtime: RuntimeReport | None

    @property
    def executed(self) -> bool:
        return self.runtime is not None


class SafetyExecutionGate:
    def __init__(
        self,
        *,
        safety_engine: SafetyEngine,
        runtime: ExecutionRuntime,
    ) -> None:
        self._safety_engine = safety_engine
        self._runtime = runtime

    def run(
        self,
        context: SafetyContext,
    ) -> SafetyExecutionResult:
        safety = self._safety_engine.evaluate(context)

        if not safety.allowed:
            return SafetyExecutionResult(
                safety=safety,
                runtime=None,
            )

        runtime = self._runtime.run(
            context.plan
        )

        return SafetyExecutionResult(
            safety=safety,
            runtime=runtime,
        )