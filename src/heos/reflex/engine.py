from .rule import ReflexRule


class ReflexEngine:

    def __init__(self):
        self.rules = []

    def register(self, rule: ReflexRule):
        self.rules.append(rule)

    def process(self, event):

        for rule in self.rules:
            if rule.event == event.event:
                return rule.action(event)

        return None