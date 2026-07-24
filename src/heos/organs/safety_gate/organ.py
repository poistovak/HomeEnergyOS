class SafetyGateOrgan:

    def __init__(self):
        self.name = "safety_gate"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
