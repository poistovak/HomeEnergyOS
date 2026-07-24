from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from heos.infrastructure.home_assistant.models import EntityMap


@dataclass(frozen=True, slots=True)
class RealHomeConfig:
    entity_map: EntityMap
    poll_interval_seconds: int = 30
    dry_run: bool = True

    @classmethod
    def from_json(cls, path: str | Path) -> RealHomeConfig:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            entity_map=EntityMap(**raw["entities"]),
            poll_interval_seconds=int(raw.get("poll_interval_seconds", 30)),
            dry_run=bool(raw.get("dry_run", True)),
        )
