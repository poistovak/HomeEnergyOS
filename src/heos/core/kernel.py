from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .config import CoreConfig
from .events import Event, EventBus
from .registry import DeviceRegistry
from .scheduler import Scheduler

StateProvider = Callable[[], Any]
DecisionProcessor = Callable[[Any], Any]

@dataclass(frozen=True, slots=True)
class TickResult:
    started_at: datetime
    finished_at: datetime
    state: Any
    decision: Any
    scheduled_tasks_run: int

    @property
    def duration_ms(self) -> float:
        return (self.finished_at - self.started_at).total_seconds() * 1000.0

class HEOSKernel:
    def __init__(self, *, state_provider: StateProvider, decision_processor: DecisionProcessor,
                 config: CoreConfig | None = None) -> None:
        self.config = config or CoreConfig()
        self.events = EventBus(history_limit=self.config.event_history_limit)
        self.registry = DeviceRegistry()
        self.scheduler = Scheduler()
        self._state_provider = state_provider
        self._decision_processor = decision_processor

    def tick(self) -> TickResult:
        started = datetime.now(UTC)
        self.events.publish(Event("kernel.tick.started"))
        due = self.scheduler.run_due(started)
        state = self._state_provider()
        self.events.publish(Event("state.updated", {"state": state}))
        decision = self._decision_processor(state)
        self.events.publish(Event("decision.created", {"decision": decision}))
        finished = datetime.now(UTC)
        result = TickResult(started, finished, state, decision, len(due))
        self.events.publish(Event("kernel.tick.completed", {"duration_ms": result.duration_ms}))
        return result
