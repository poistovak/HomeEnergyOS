from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable
from uuid import UUID, uuid4

TaskCallback = Callable[[], None]

@dataclass(order=True, frozen=True, slots=True)
class ScheduledTask:
    run_at: datetime
    callback: TaskCallback = field(compare=False, repr=False)
    name: str = field(default="task", compare=False)
    task_id: UUID = field(default_factory=uuid4, compare=False)

class Scheduler:
    def __init__(self) -> None:
        self._tasks: list[ScheduledTask] = []

    def schedule(self, task: ScheduledTask) -> None:
        if task.run_at.tzinfo is None:
            raise ValueError("run_at must be timezone-aware")
        self._tasks.append(task)
        self._tasks.sort()

    def run_due(self, now: datetime | None = None) -> tuple[ScheduledTask, ...]:
        current = now or datetime.now(UTC)
        due = tuple(t for t in self._tasks if t.run_at <= current)
        self._tasks = [t for t in self._tasks if t.run_at > current]
        for task in due:
            task.callback()
        return due
