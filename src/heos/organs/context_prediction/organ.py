class ContextPredictionOrgan:

    def __init__(self):
        self.name = "context_prediction"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
