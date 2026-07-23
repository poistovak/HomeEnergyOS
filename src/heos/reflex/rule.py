from dataclasses import dataclass
from collections.abc import Callable


@dataclass
class ReflexRule:
    event: str
    action: Callable