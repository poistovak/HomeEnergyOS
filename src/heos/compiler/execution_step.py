from dataclasses import dataclass
from enum import StrEnum

class StepType(StrEnum):
    VERIFY="verify"
    WAIT="wait"
    SET_CURRENT="set_current"

@dataclass(frozen=True, slots=True)
class ExecutionStep:
    step_type: StepType
    description: str
