"""Immutable input context for safety evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from heos.compiler.execution_plan import ExecutionPlan
from heos.kernel import KernelSnapshot


@dataclass(frozen=True, slots=True)
class SafetyContext:
    plan: ExecutionPlan
    kernel: KernelSnapshot
    manual_lock: bool = False
    projected_grid_import_w: float = 0.0
    maximum_grid_import_w: float | None = None

    def __post_init__(self) -> None:
        if self.projected_grid_import_w < 0:
            raise ValueError(
                "projected_grid_import_w cannot be negative"
            )
        if (
            self.maximum_grid_import_w is not None
            and self.maximum_grid_import_w < 0
        ):
            raise ValueError(
                "maximum_grid_import_w cannot be negative"
            )
