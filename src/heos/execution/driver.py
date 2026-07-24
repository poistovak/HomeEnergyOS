from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from heos.compiler.execution_step import ExecutionStep


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    success: bool
    message: str = ""
    observed_value: object | None = None

class ExecutionDriver(Protocol):
    def execute(self, step: ExecutionStep) -> ExecutionResult:
        """Execute one abstract step."""
