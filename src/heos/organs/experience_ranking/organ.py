class ExperienceRankingOrgan:

    def __init__(self):
        self.name = "experience_ranking"
        self.status = "initialized"

    def activate(self):
        self.status = "active"
        return self.status
