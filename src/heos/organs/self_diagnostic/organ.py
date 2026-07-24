class SelfDiagnosticOrgan:

    def __init__(self):
        self.name = "self_diagnostic"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
