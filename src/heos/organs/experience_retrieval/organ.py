class ExperienceRetrievalOrgan:

    def __init__(self):
        self.name = "experience_retrieval"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
