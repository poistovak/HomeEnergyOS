class PlanOptimizationOrgan:

    def __init__(self):
        self.name = "plan_optimization"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
