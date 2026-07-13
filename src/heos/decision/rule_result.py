from dataclasses import dataclass

@dataclass(frozen=True)
class RuleResult:

    matched: bool

    score: float