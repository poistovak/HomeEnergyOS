from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


@dataclass(slots=True)
class CapabilityMetadata:
    id: str
    name: str
    version: str = "1.0"
    description: str = ""


class Capability(ABC):
    """Base class for every HEOS capability."""

    metadata: CapabilityMetadata