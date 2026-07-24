from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoreConfig:
    tick_interval_seconds: int = 30
    event_history_limit: int = 500
    dry_run: bool = True

    def __post_init__(self) -> None:
        if self.tick_interval_seconds <= 0:
            raise ValueError("tick_interval_seconds must be positive")
        if self.event_history_limit < 1:
            raise ValueError("event_history_limit must be at least 1")
