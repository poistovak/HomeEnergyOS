from __future__ import annotations

from dataclasses import dataclass, field

from .models import VerificationDecision


@dataclass(slots=True)
class VerificationLedger:
    _entries: list[VerificationDecision] = field(default_factory=list)

    def append(self, decision: VerificationDecision) -> None:
        if self._entries and self._entries[-1].verification_id == decision.verification_id:
            return
        self._entries.append(decision)

    def entries(self) -> tuple[VerificationDecision, ...]:
        return tuple(self._entries)

    def latest_for(self, command_id: str) -> VerificationDecision | None:
        for decision in reversed(self._entries):
            if decision.command_id == command_id:
                return decision
        return None
