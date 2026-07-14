from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


@dataclass(slots=True)
class CapabilityMetadata:
    name: str
    version: str = "1.0"
    description: str = ""


class Capability(ABC):
    """
    Base class for every HEOS capability.

    Brains never communicate with concrete devices.
    They communicate only with Capabilities.
    """

    metadata: CapabilityMetadata