from dataclasses import dataclass

@dataclass(frozen=True)
class Constraint:

    description: str