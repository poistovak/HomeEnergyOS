from dataclasses import dataclass


@dataclass(frozen=True)
class Violation:

    message: str

    severity: str