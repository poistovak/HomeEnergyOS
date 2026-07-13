"""Brain API for HEOS.

Brains inspect a normalized HouseState and propose candidate decisions.
They never execute device actions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from .decision import Decision
from .state import HouseState


class Brain(Protocol):
    """Public contract implemented by every HEOS brain."""

    brain_id: str

    def propose(self, state: HouseState) -> tuple[Decision, ...]:
        """Return zero or more candidate decisions."""


@dataclass(frozen=True, slots=True)
class BrainMetadata:
    """Metadata shown in diagnostics and future plugin discovery."""

    brain_id: str
    name: str
    version: str
    description: str


class BaseBrain(ABC):
    """Convenience base class for built-in brains."""

    metadata: BrainMetadata

    @property
    def brain_id(self) -> str:
        return self.metadata.brain_id

    @abstractmethod
    def propose(self, state: HouseState) -> tuple[Decision, ...]:
        """Return candidate decisions without side effects."""
