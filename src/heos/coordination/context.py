from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class CoordinationContext:
    """Shared context for one coordinated HEOS cycle."""

    cycle_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = "unknown"
    request: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    state: str = "CREATED"
