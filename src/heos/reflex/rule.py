from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ReflexRule:
    event: str
    action: Callable