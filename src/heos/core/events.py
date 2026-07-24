from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

EventHandler = Callable[["Event"], None]

@dataclass(frozen=True, slots=True)
class Event:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_id: UUID = field(default_factory=uuid4)

class EventBus:
    def __init__(self, *, history_limit: int = 500) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: deque[Event] = deque(maxlen=history_limit)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        if handler not in self._handlers[topic]:
            self._handlers[topic].append(handler)

    def publish(self, event: Event) -> None:
        self._history.append(event)
        for handler in tuple(self._handlers.get(event.topic, ())):
            handler(event)
        for handler in tuple(self._handlers.get("*", ())):
            handler(event)

    @property
    def history(self) -> tuple[Event, ...]:
        return tuple(self._history)
