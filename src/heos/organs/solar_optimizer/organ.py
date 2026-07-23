class SolarOptimizerOrgan:

    def __init__(self):
        self.name = "solar_optimizer"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
