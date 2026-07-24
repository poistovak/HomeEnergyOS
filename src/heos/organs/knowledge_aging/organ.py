class KnowledgeAgingOrgan:

    def __init__(self):
        self.name = "knowledge_aging"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
