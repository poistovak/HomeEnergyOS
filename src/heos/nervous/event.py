from dataclasses import dataclass
from typing import Any


@dataclass
class OrganEvent:
    source: str
    event: str
    data: dict[str, Any]