from dataclasses import dataclass

@dataclass(frozen=True)
class Policy:

    name: str

    enabled: bool = True