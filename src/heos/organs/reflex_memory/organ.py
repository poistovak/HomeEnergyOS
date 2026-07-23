class ReflexMemoryOrgan:

    def __init__(self):
        self.name = "reflex_memory"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
