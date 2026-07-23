class OrganRegistryOrgan:

    def __init__(self):
        self.name = "organ_registry"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
