from .execution_plan import ExecutionPlan
from .execution_step import ExecutionStep, StepType


class DecisionCompiler:
    def compile(self, scenario_id:str)->ExecutionPlan:
        if scenario_id=="charge_ev_now":
            steps=(
                ExecutionStep(StepType.VERIFY,"Kernel READY"),
                ExecutionStep(StepType.VERIFY,"EV connected"),
                ExecutionStep(StepType.WAIT,"Wait 60 seconds"),
                ExecutionStep(StepType.SET_CURRENT,"Set charger current to 6 A"),
                ExecutionStep(StepType.VERIFY,"Verify charging current"),
            )
        else:
            steps=(ExecutionStep(StepType.VERIFY,"No-op verification"),)
        return ExecutionPlan(scenario_id=scenario_id, steps=steps)
