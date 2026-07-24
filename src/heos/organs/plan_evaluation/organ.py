class PlanEvaluationOrgan:

    def __init__(self):
        self.name = "plan_evaluation"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
