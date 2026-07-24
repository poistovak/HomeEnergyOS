class RecoveryVerificationOrgan:

    def __init__(self):
        self.name = "recovery_verification"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
