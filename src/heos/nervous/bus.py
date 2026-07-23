from collections.abc import Callable

from .event import OrganEvent


class OrganBus:

    def __init__(self):
        self.listeners: list[Callable[[OrganEvent], None]] = []

    def subscribe(self, listener):
        self.listeners.append(listener)

    def publish(self, event: OrganEvent):

        for listener in self.listeners:
            listener(event)