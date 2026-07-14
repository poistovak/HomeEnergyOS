from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from .capability import Capability, CapabilityMetadata


@dataclass(slots=True)
class ProducerState:
    power: float
    today_energy: float
    online: bool


class EnergyProducerCapability(Capability):
     id="energy_producer",
    name="Energy Producer",
    version="1.0",
    description="..."

    @abstractmethod
    def state(self) -> ProducerState:
        """Return current production state."""