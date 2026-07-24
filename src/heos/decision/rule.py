from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:

    name: str

    priority: int