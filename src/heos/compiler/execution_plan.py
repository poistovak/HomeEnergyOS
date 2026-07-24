from dataclasses import dataclass

from .execution_step import ExecutionStep


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    scenario_id: str
    steps: tuple[ExecutionStep,...]
