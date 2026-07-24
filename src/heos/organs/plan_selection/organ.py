class PlanSelectionOrgan:

    def __init__(self):
        self.name = "plan_selection"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
